import pytest
from aiqleads.data.cleaner import DataCleaner, CleaningRule, RuleType

@pytest.fixture
def cleaner():
    return DataCleaner()

@pytest.fixture
def basic_rules():
    return [
        CleaningRule(field_name="email", rule_type=RuleType.EMAIL),
        CleaningRule(field_name="phone", rule_type=RuleType.PHONE),
        CleaningRule(field_name="name", rule_type=RuleType.TEXT),
        CleaningRule(field_name="price", rule_type=RuleType.NUMERIC),
        CleaningRule(field_name="address", rule_type=RuleType.ADDRESS),
        CleaningRule(field_name="website", rule_type=RuleType.URL),
    ]

def test_email_normalization(cleaner, basic_rules):
    data = {"email": " TEST@EXAMPLE.COM "}
    result = cleaner.clean(data, [r for r in basic_rules if r.field_name == "email"])
    assert result["email"] == "test@example.com"

def test_invalid_email(cleaner, basic_rules):
    data = {"email": "invalid-email"}
    with pytest.raises(ValueError, match="Invalid email address"):
        cleaner.clean(data, [r for r in basic_rules if r.field_name == "email"])

def test_phone_normalization(cleaner, basic_rules):
    data = {"phone": "(123) 456-7890"}
    result = cleaner.clean(data, [r for r in basic_rules if r.field_name == "phone"])
    assert result["phone"] == "+11234567890"

def test_invalid_phone(cleaner, basic_rules):
    data = {"phone": "invalid-phone"}
    with pytest.raises(ValueError, match="Invalid phone number format"):
        cleaner.clean(data, [r for r in basic_rules if r.field_name == "phone"])

def test_text_normalization(cleaner, basic_rules):
    data = {"name": " john doe "}
    result = cleaner.clean(data, [r for r in basic_rules if r.field_name == "name"])
    assert result["name"] == "John Doe"

def test_numeric_normalization(cleaner, basic_rules):
    data = {"price": "$1,234.56"}
    result = cleaner.clean(data, [r for r in basic_rules if r.field_name == "price"])
    assert result["price"] == 1234.56

def test_invalid_numeric(cleaner, basic_rules):
    data = {"price": "invalid-price"}
    with pytest.raises(ValueError, match="Invalid numeric value"):
        cleaner.clean(data, [r for r in basic_rules if r.field_name == "price"])

def test_address_normalization(cleaner, basic_rules):
    data = {"address": " 123 Main St "}
    result = cleaner.clean(data, [r for r in basic_rules if r.field_name == "address"])
    assert result["address"] == "123 Main St"

def test_url_normalization(cleaner, basic_rules):
    data = {"website": "https://example.com"}
    result = cleaner.clean(data, [r for r in basic_rules if r.field_name == "website"])
    assert result["website"] == "https://example.com"

def test_invalid_url(cleaner, basic_rules):
    data = {"website": "not-a-url"}
    with pytest.raises(ValueError, match="Invalid URL"):
        cleaner.clean(data, [r for r in basic_rules if r.field_name == "website"])

def test_required_field_missing(cleaner):
    rule = CleaningRule(field_name="email", rule_type=RuleType.EMAIL, required=True)
    data = {}
    with pytest.raises(ValueError, match="Missing required field"):
        cleaner.clean(data, [rule])

def test_optional_field_missing(cleaner):
    rule = CleaningRule(field_name="email", rule_type=RuleType.EMAIL, required=False)
    data = {}
    result = cleaner.clean(data, [rule])
    assert result["email"] is None

def test_multiple_fields(cleaner, basic_rules):
    data = {
        "email": "test@example.com",
        "phone": "(123) 456-7890",
        "name": "john doe",
        "price": "$1,234.56",
        "address": "123 Main St",
        "website": "https://example.com"
    }
    result = cleaner.clean(data, basic_rules)
    assert all(field in result for field in data.keys())
    assert result["email"] == "test@example.com"
    assert result["phone"] == "+11234567890"
    assert result["name"] == "John Doe"
    assert result["price"] == 1234.56
    assert result["address"] == "123 Main St"
    assert result["website"] == "https://example.com"

def test_invalid_rule_type():
    with pytest.raises(ValueError, match="Unsupported rule type"):
        CleaningRule(field_name="test", rule_type="invalid_type")

def test_empty_field_name():
    with pytest.raises(ValueError, match="Field name cannot be empty"):
        CleaningRule(field_name="", rule_type=RuleType.TEXT)