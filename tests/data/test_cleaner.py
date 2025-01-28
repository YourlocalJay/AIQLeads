import pytest
from datetime import datetime
from aiqleads.data.cleaner import (
    LeadDataCleaner,
    BatchDataCleaner,
    CleaningRule,
    RuleType
)

@pytest.fixture
def lead_cleaner():
    return LeadDataCleaner()

# ... [rest of the test implementation] ...