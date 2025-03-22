import json
import unittest
from unittest.mock import patch, MagicMock
from tests.test_processor import ProcessorLambdaTestCase
from ..lambdas.processor import HANDLER  # Use relative import



class TestSuccess(ProcessorLambdaTestCase):

    @patch("requests.get")
    @patch("boto3.resource")
    def test_success(self, mock_dynamodb_resource, mock_requests_get):
        # Mock API response from Open-Meteo
        mock_requests_get.return_value.status_code = 200
        mock_requests_get.return_value.json.return_value = {
            "elevation": 34.0,
            "generationtime_ms": 123.45,
            "hourly": {
                "temperature_2m": [22.5, 23.1],
                "time": ["2025-03-22T12:00", "2025-03-22T13:00"]
            },
            "hourly_units": {
                "temperature_2m": "°C",
                "time": "ISO8601"
            },
            "latitude": 52.52,
            "longitude": 13.41,
            "timezone": "Europe/Berlin",
            "timezone_abbreviation": "CET",
            "utc_offset_seconds": 3600
        }

        # Mock DynamoDB table put_item method
        mock_table = MagicMock()
        mock_dynamodb_resource.return_value.Table.return_value = mock_table
        mock_table.put_item.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}

        # Call the Lambda handler
        response = HANDLER.handle_request({}, {})

        # Validate the response
        self.assertEqual(response["statusCode"], 200)
        body = json.loads(response["body"])
        self.assertIn("message", body)
        self.assertEqual(body["message"], "Weather data stored successfully!")

        # Ensure API was called
        mock_requests_get.assert_called_once()

        # Ensure data was written to DynamoDB
        mock_table.put_item.assert_called_once()


if __name__ == "__main__":
    unittest.main()
