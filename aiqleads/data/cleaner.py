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

# ... [rest of the cleaner.py implementation] ...