import json
from copy import deepcopy

import pytest
from unittest.mock import patch
from validation import validator

VALID_EVENT = {
    "street_name": "Südosttangente (A23)",
    "street_id": "VIE-001",
    "camera_id": "CAM-VIE-001-01",
    "timestamp": "2025-12-15T14:36:04.272179",
    "license_plate": "OZ 638IS",
    "speed_kph": 80.9,
    "speed_limit": 80,
    "lane_id": 1,
    "vehicle_type": "Bus",
    "ocr_confidence": 0.91,
    "is_violation": True,
}


def test_validate_schema_valid():
    is_valid, error_message = validator.validate_schema(VALID_EVENT)
    assert is_valid
    assert error_message is None


@pytest.mark.parametrize("missing", VALID_EVENT.keys())
def test_validate_schema_missing_field(missing):
    event = deepcopy(VALID_EVENT)
    del event[missing]
    is_valid, error_message = validator.validate_schema(event)
    assert not is_valid
    assert missing in error_message


@pytest.mark.parametrize("field", ["street_name", "street_id"])
def test_validate_data_empty_string(field):
    event = deepcopy(VALID_EVENT)
    event[field] = ""
    is_valid, error_message = validator.validate_data(event)
    assert not is_valid
    assert f"{field} cannot be empty" in error_message


def test_validate_data_camera_id_invalid():
    event = deepcopy(VALID_EVENT)
    event["camera_id"] = "badId"
    is_valid, error_message = validator.validate_data(event)
    assert not is_valid
    assert "camera_id format is invalid" in error_message


def test_validate_data_timestamp_invalid():
    event = deepcopy(VALID_EVENT)
    event["timestamp"] = "invalid-timestamp"
    is_valid, error_message = validator.validate_data(event)
    assert not is_valid
    assert "timestamp format is invalid" in error_message


def test_validate_data_license_plate_invalid():
    event = deepcopy(VALID_EVENT)
    event["license_plate"] = "AAA-123"
    is_valid, error_message = validator.validate_data(event)
    assert not is_valid
    assert "license_plate format is invalid" in error_message


def test_validate_data_speed_negative():
    event = deepcopy(VALID_EVENT)
    event["speed_kph"] = -10
    is_valid, error_message = validator.validate_data(event)
    assert not is_valid
    assert "Invalid speed_kph value" in error_message


def test_validate_data_speed_limit_too_high():
    event = deepcopy(VALID_EVENT)
    event["speed_limit"] = 400
    is_valid, error_message = validator.validate_data(event)
    assert not is_valid
    assert "Invalid speed_kph value" in error_message


def test_validate_data_lane_id_invalid():
    event = deepcopy(VALID_EVENT)
    event["lane_id"] = 0
    is_valid, error_message = validator.validate_data(event)
    assert not is_valid
    assert "lane_id must be >= 1" in error_message


def test_validate_data_vehicle_type_unknown():
    event = deepcopy(VALID_EVENT)
    event["vehicle_type"] = "Boat"
    is_valid, error_message = validator.validate_data(event)
    assert not is_valid
    assert "Unknown vehicle_type" in error_message


def test_validate_data_ocr_confidence_too_low():
    event = deepcopy(VALID_EVENT)
    event["ocr_confidence"] = 0.4
    is_valid, error_message = validator.validate_data(event)
    assert not is_valid
    assert "ocr_confidence is too low" in error_message


def test_validate_data_ocr_confidence_too_high():
    event = deepcopy(VALID_EVENT)
    event["ocr_confidence"] = 1.5
    is_valid, error_message = validator.validate_data(event)
    assert not is_valid
    assert "ocr_confidence cannot be greater than 1.0" in error_message


def test_handler_valid_event():
    with patch('validation.validator.forward_to_aggregation') as mock_forward:
        response = validator.lambda_handler(VALID_EVENT, None)
        assert response['statusCode'] == 202
        mock_forward.assert_called_once_with(VALID_EVENT)


def test_handler_invalid_schema():
    invalid_event = deepcopy(VALID_EVENT)
    del invalid_event["street_name"]
    response = validator.lambda_handler(invalid_event, None)
    assert response['statusCode'] == 400
    body = json.loads(response['body'])
    assert 'error' in body


def test_handler_invalid_data():
    invalid_event = deepcopy(VALID_EVENT)
    invalid_event["speed_kph"] = -5
    response = validator.lambda_handler(invalid_event, None)
    assert response['statusCode'] == 422
    body = json.loads(response['body'])
    assert 'error' in body
