from typing import Dict, Any, List, Optional, Set
from datetime import datetime
import logging
import re
from enum import Enum
import phonenumbers
from email_validator import validate_email, EmailNotValidError
from pydantic import BaseModel, Field, validator
import validators
import pandas as pd
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class RuleType(str, Enum):
    """Enumeration of supported cleaning rule types"""
    EMAIL = "email_normalize"
    PHONE = "phone_normalize"
    TEXT = "text_normalize"
    NUMERIC = "numeric_normalize"
    ADDRESS = "address_normalize"
    URL = "url_normalize"

class CleaningRule(BaseModel):
    """Represents a rule for normalizing or validating data."""
    field_name: str
    rule_type: RuleType
    required: bool = True

    @validator("field_name")
    def validate_field_name(cls, value):
        if not value.strip():
            raise ValueError("Field name cannot be empty.")
        return value

    @validator("rule_type")
    def validate_rule_type(cls, value):
        if value not in RuleType.__members__.values():
            raise ValueError(f"Unsupported rule type: {value}")
        return value

class BaseCleaner(ABC):
    """Abstract base class for all cleaners."""

    @abstractmethod
    def clean(self, data: Dict[str, Any], rules: List[CleaningRule]) -> Dict[str, Any]:
        pass

class DataCleaner(BaseCleaner):
    """Implements data normalization and cleaning rules."""

    def clean(self, data: Dict[str, Any], rules: List[CleaningRule]) -> Dict[str, Any]:
        """
        Apply cleaning rules to the provided data.

        Args:
            data (Dict[str, Any]): The raw data to clean.
            rules (List[CleaningRule]): List of cleaning rules.

        Returns:
            Dict[str, Any]: The cleaned data.
        """
        cleaned_data = {}
        for rule in rules:
            try:
                value = data.get(rule.field_name)
                if rule.required and value is None:
                    raise ValueError(f"Missing required field: {rule.field_name}")

                if value is not None:
                    if rule.rule_type == RuleType.EMAIL:
                        cleaned_data[rule.field_name] = self._normalize_email(value)
                    elif rule.rule_type == RuleType.PHONE:
                        cleaned_data[rule.field_name] = self._normalize_phone(value)
                    elif rule.rule_type == RuleType.TEXT:
                        cleaned_data[rule.field_name] = self._normalize_text(value)
                    elif rule.rule_type == RuleType.NUMERIC:
                        cleaned_data[rule.field_name] = self._normalize_numeric(value)
                    elif rule.rule_type == RuleType.ADDRESS:
                        cleaned_data[rule.field_name] = self._normalize_address(value)
                    elif rule.rule_type == RuleType.URL:
                        cleaned_data[rule.field_name] = self._normalize_url(value)
                else:
                    cleaned_data[rule.field_name] = None

            except Exception as e:
                logger.warning(f"Failed to clean field '{rule.field_name}': {e}")
                if rule.required:
                    raise

        return cleaned_data

    @staticmethod
    def _normalize_email(email: str) -> str:
        """Normalize and validate email addresses."""
        try:
            valid_email = validate_email(email)
            return valid_email.email
        except EmailNotValidError as e:
            raise ValueError(f"Invalid email address: {email}")

    @staticmethod
    def _normalize_phone(phone: str) -> str:
        """Normalize and validate phone numbers."""
        try:
            parsed_phone = phonenumbers.parse(phone, "US")  # Adjust region as needed
            if not phonenumbers.is_valid_number(parsed_phone):
                raise ValueError(f"Invalid phone number: {phone}")
            return phonenumbers.format_number(parsed_phone, phonenumbers.PhoneNumberFormat.E164)
        except phonenumbers.NumberParseException:
            raise ValueError(f"Invalid phone number format: {phone}")

    @staticmethod
    def _normalize_text(text: str) -> str:
        """Normalize text by trimming whitespace and standardizing case."""
        return text.strip().title()

    @staticmethod
    def _normalize_numeric(value: Any) -> float:
        """Normalize numeric values, ensuring proper formatting."""
        try:
            return float(re.sub(r"[^0-9.]+", "", str(value)))
        except ValueError:
            raise ValueError(f"Invalid numeric value: {value}")

    @staticmethod
    def _normalize_address(address: str) -> str:
        """Normalize and validate address strings."""
        return address.strip()

    @staticmethod
    def _normalize_url(url: str) -> str:
        """Normalize and validate URLs."""
        if not validators.url(url):
            raise ValueError(f"Invalid URL: {url}")
        return url

if __name__ == "__main__":
    # Example usage
    rules = [
        CleaningRule(field_name="email", rule_type=RuleType.EMAIL),
        CleaningRule(field_name="phone", rule_type=RuleType.PHONE),
        CleaningRule(field_name="price", rule_type=RuleType.NUMERIC),
    ]

    raw_data = {
        "email": " TEST@example.COM ",
        "phone": "(123) 456-7890",
        "price": "$1,200.50",
    }

    cleaner = DataCleaner()
    cleaned_data = cleaner.clean(raw_data, rules)
    print(cleaned_data)
