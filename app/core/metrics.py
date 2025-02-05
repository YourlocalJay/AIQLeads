"""
Prometheus metrics configuration for feature extraction and caching.
"""

from prometheus_client import Counter, Histogram

# Feature extraction metrics
FEATURE_EXTRACTION_TIME = Histogram(
    "feature_extraction_seconds", "Time spent extracting features", ["extractor_type"]
)

FEATURE_EXTRACTION_ERRORS = Counter(
    "feature_extraction_errors_total",
    "Number of feature extraction errors",
    ["extractor_type", "error_type"],
)

FEATURE_COUNT = Counter(
    "features_extracted_total", "Number of features extracted", ["extractor_type"]
)

# Cache metrics
CACHE_HIT_COUNTER = Counter("cache_hits_total", "Number of cache hits", ["cache_type"])

CACHE_MISS_COUNTER = Counter(
    "cache_misses_total", "Number of cache misses", ["cache_type"]
)

# Validation metrics
VALIDATION_ERRORS = Counter(
    "validation_errors_total",
    "Number of validation errors",
    ["validator_type", "error_type"],
)

VALIDATION_TIME = Histogram(
    "validation_seconds", "Time spent on validation", ["validator_type"]
)
