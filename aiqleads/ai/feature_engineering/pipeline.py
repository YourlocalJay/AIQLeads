from typing import List, Dict, Any, Optional, Type
from pydantic import BaseModel
import importlib
import logging
import asyncio
from datetime import datetime

from .preprocessors import BasePreprocessor
from .extractors import BaseFeatureExtractor
from .validators import BaseValidator
from .storage import FeatureStore
from .exceptions import (
    PipelineConfigError,
    PreprocessingError,
    FeatureExtractionError,
    ValidationError as FeatureValidationError,
)

logger = logging.getLogger(__name__)


class ComponentConfig(BaseModel):
    """Base configuration for pipeline components."""

    type: str
    config: Dict[str, Any]


class FeatureEngineeringConfig(BaseModel):
    """Configuration for the feature engineering pipeline."""

    preprocessing_steps: List[ComponentConfig]
    feature_extractors: List[ComponentConfig]
    validation_rules: List[ComponentConfig]
    storage_config: Dict[str, Any]
    cache_config: Optional[Dict[str, Any]] = None
    batch_size: int = 100
    max_retries: int = 3
    skip_invalid_leads: bool = True


class PipelineMetrics:
    """Tracks pipeline processing metrics."""

    def __init__(self):
        self.processed_leads = 0
        self.failed_leads = 0
        self.features_generated = 0
        self.validation_failures = 0
        self.processing_times: List[float] = []
        self.start_time = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary format."""
        avg_processing_time = (
            sum(self.processing_times) / len(self.processing_times)
            if self.processing_times
            else 0
        )
        return {
            "processed_leads": self.processed_leads,
            "failed_leads": self.failed_leads,
            "features_generated": self.features_generated,
            "validation_failures": self.validation_failures,
            "average_processing_time_ms": avg_processing_time,
            "uptime_seconds": (datetime.now() - self.start_time).total_seconds(),
        }


class FeatureEngineeringPipeline:
    """Main pipeline for feature engineering process."""

    def __init__(self, config: FeatureEngineeringConfig):
        """Initialize the pipeline with configuration."""
        self.config = config
        self.preprocessors: List[BasePreprocessor] = []
        self.extractors: List[BaseFeatureExtractor] = []
        self.validators: List[BaseValidator] = []
        self.feature_store = FeatureStore(config.storage_config)
        self.metrics = PipelineMetrics()

        try:
            self._initialize_components()
        except Exception as e:
            raise PipelineConfigError(f"Failed to initialize pipeline: {str(e)}")

    def _load_component_class(self, component_type: str, base_class: Type) -> Type:
        """Dynamically load a component class."""
        try:
            module_path, class_name = component_type.rsplit(".", 1)
            module = importlib.import_module(module_path)
            component_class = getattr(module, class_name)

            if not issubclass(component_class, base_class):
                raise PipelineConfigError(
                    f"Component {component_type} must inherit from {base_class.__name__}"
                )

            return component_class
        except (ImportError, AttributeError) as e:
            raise PipelineConfigError(
                f"Failed to load component {component_type}: {str(e)}"
            )

    def _initialize_components(self) -> None:
        """Initialize all pipeline components from config."""
        # Initialize preprocessors
        for step_config in self.config.preprocessing_steps:
            preprocessor_class = self._load_component_class(
                step_config.type, BasePreprocessor
            )
            self.preprocessors.append(preprocessor_class(**step_config.config))

        # Initialize extractors
        for extractor_config in self.config.feature_extractors:
            extractor_class = self._load_component_class(
                extractor_config.type, BaseFeatureExtractor
            )
            self.extractors.append(extractor_class(**extractor_config.config))

        # Initialize validators
        for validator_config in self.config.validation_rules:
            validator_class = self._load_component_class(
                validator_config.type, BaseValidator
            )
            self.validators.append(validator_class(**validator_config.config))

    async def _apply_preprocessing(self, lead_data: Dict[str, Any]) -> Dict[str, Any]:
        """Apply all preprocessing steps to a lead."""
        processed_data = lead_data.copy()

        for preprocessor in self.preprocessors:
            try:
                processed_data = await preprocessor.process(processed_data)
            except Exception as e:
                raise PreprocessingError(
                    f"Preprocessing failed for lead {lead_data.get('id', 'unknown')}: {str(e)}"
                )

        return processed_data

    async def _extract_features(self, processed_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract features using all extractors."""
        features = {}

        for extractor in self.extractors:
            try:
                extracted = await extractor.extract(processed_data)
                features.update(extracted)
            except Exception as e:
                raise FeatureExtractionError(
                    f"Feature extraction failed for lead {processed_data.get('id', 'unknown')}: {str(e)}"
                )

        return features

    async def _validate_features(self, features: Dict[str, Any]) -> bool:
        """Validate extracted features using all validators."""
        for validator in self.validators:
            try:
                if not await validator.validate(features):
                    self.metrics.validation_failures += 1
                    return False
            except Exception as e:
                raise FeatureValidationError(f"Feature validation failed: {str(e)}")

        return True

    async def process_lead(self, lead_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Process a single lead through the feature engineering pipeline."""
        start_time = datetime.now()

        try:
            # Apply preprocessing
            processed_data = await self._apply_preprocessing(lead_data)

            # Extract features
            features = await self._extract_features(processed_data)

            # Validate features
            if not await self._validate_features(features):
                logger.warning(
                    f"Feature validation failed for lead {lead_data.get('id', 'unknown')}"
                )
                return None

            # Store features
            await self.feature_store.store_features(lead_data["id"], features)

            # Update metrics
            self.metrics.processed_leads += 1
            self.metrics.features_generated += len(features)
            processing_time = (datetime.now() - start_time).total_seconds() * 1000
            self.metrics.processing_times.append(processing_time)

            return features

        except Exception as e:
            self.metrics.failed_leads += 1
            logger.error(
                f"Failed to process lead {lead_data.get('id', 'unknown')}: {str(e)}"
            )
            if not self.config.skip_invalid_leads:
                raise
            return None

    async def process_batch(self, leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process a batch of leads through the pipeline."""
        tasks = []
        for i in range(0, len(leads), self.config.batch_size):
            batch = leads[i : i + self.config.batch_size]
            tasks.extend([self.process_lead(lead) for lead in batch])

        results = await asyncio.gather(*tasks, return_exceptions=True)
        return [r for r in results if isinstance(r, dict)]

    def get_feature_metadata(self) -> Dict[str, Any]:
        """Get metadata about the features being generated."""
        feature_names = []
        for extractor in self.extractors:
            feature_names.extend(extractor.get_feature_names())

        return {
            "features": {"total_count": len(feature_names), "names": feature_names},
            "preprocessing": {
                "steps": len(self.preprocessors),
                "types": [p.__class__.__name__ for p in self.preprocessors],
            },
            "validation": {
                "rules": len(self.validators),
                "types": [v.__class__.__name__ for v in self.validators],
            },
            "metrics": self.metrics.to_dict(),
            "storage": self.feature_store.get_storage_info(),
        }
