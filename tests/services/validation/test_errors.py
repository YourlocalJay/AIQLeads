from src.services.validation.errors import (
    ValidationError,
    ValidationErrorType,
    handle_validation_error,
)


def test_validation_error_creation():
    error = ValidationError(
        error_type=ValidationErrorType.SCHEMA_ERROR,
        message="Invalid schema",
        field="email",
        details={"constraint": "format"},
    )

    assert error.error_type == ValidationErrorType.SCHEMA_ERROR
    assert error.message == "Invalid schema"
    assert error.field == "email"
    assert error.details == {"constraint": "format"}


def test_validation_error_to_dict():
    error = ValidationError(
        error_type=ValidationErrorType.DATA_TYPE_ERROR,
        message="Invalid type",
        field="age",
    )

    error_dict = error.to_dict()
    assert error_dict["error_type"] == "data_type_error"
    assert error_dict["message"] == "Invalid type"
    assert error_dict["field"] == "age"


def test_handle_validation_error():
    error = ValidationError(
        error_type=ValidationErrorType.MISSING_FIELD, message="Required field missing"
    )

    response = handle_validation_error(error)
    assert response["status"] == "error"
    assert response["code"] == "VALIDATION_ERROR"
    assert response["message"] == "Required field missing"
