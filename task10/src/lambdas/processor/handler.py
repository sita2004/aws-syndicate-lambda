import json
import uuid
import os
import requests
import boto3
from aws_xray_sdk.core import patch_all, xray_recorder
from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda

# Enable AWS X-Ray tracing
patch_all()

_LOG = get_logger(__name__)

# Get the DynamoDB table name from environment variables
DYNAMODB_TABLE = os.getenv("target_table", "Weather")

# Validate if the table exists
_LOG.info(f"Using DynamoDB table: {DYNAMODB_TABLE}")

# Initialize AWS services
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(DYNAMODB_TABLE)

# Open-Meteo API URL
WEATHER_API_URL = (
    "https://api.open-meteo.com/v1/forecast?"
    "latitude=52.52&longitude=13.41&current=temperature_2m,wind_speed_10m"
    "&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"
)


class Processor(AbstractLambda):
    def validate_request(self, event) -> dict:
        """
        Validate the incoming event structure (if necessary)
        """
        return {}

    def handle_request(self, event, context):
        """
        Lambda function that fetches the latest weather forecast and stores it in DynamoDB.
        """

        _LOG.info(f"Fetching weather data from Open-Meteo API for table: {DYNAMODB_TABLE}")
        xray_recorder.begin_segment("WeatherLambdaFunction")

        try:
            # Fetch weather data from Open-Meteo API
            response = requests.get(WEATHER_API_URL)
            response.raise_for_status()
            weather_data = response.json()

            # Debug API response structure
            _LOG.info(f"Received API Data: {json.dumps(weather_data, indent=2)}")

            # Ensure all required fields exist before accessing them
            if "hourly" not in weather_data or "hourly_units" not in weather_data:
                raise ValueError("Missing expected fields in Open-Meteo response")

            # Generate a unique ID
            item_id = str(uuid.uuid4())

            # Format data to match DynamoDB schema
            item = {
                "id": item_id,
                "forecast": {
                    "elevation": weather_data.get("elevation", 0),
                    "generationtime_ms": weather_data.get("generationtime_ms", 0),
                    "hourly": {
                        "temperature_2m": weather_data["hourly"].get("temperature_2m", []),
                        "time": weather_data["hourly"].get("time", [])
                    },
                    "hourly_units": {
                        "temperature_2m": weather_data["hourly_units"].get("temperature_2m", "°C"),
                        "time": weather_data["hourly_units"].get("time", "ISO8601")
                    },
                    "latitude": weather_data.get("latitude", 0),
                    "longitude": weather_data.get("longitude", 0),
                    "timezone": weather_data.get("timezone", ""),
                    "timezone_abbreviation": weather_data.get("timezone_abbreviation", ""),
                    "utc_offset_seconds": weather_data.get("utc_offset_seconds", 0)
                }
            }

            # Log the formatted item before inserting it
            _LOG.info(f"Formatted DynamoDB Item: {json.dumps(item, indent=2)}")

            # Store the data in DynamoDB
            put_response = table.put_item(Item=item)

            # Log DynamoDB response
            _LOG.info(f"DynamoDB PutItem Response: {put_response}")

            # Check if data was successfully stored
            if put_response["ResponseMetadata"]["HTTPStatusCode"] != 200:
                raise Exception("DynamoDB put_item failed")

            xray_recorder.end_segment()

            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "Weather data stored successfully!",
                    "id": item_id
                })
            }

        except Exception as e:
            _LOG.error(f"Error processing request: {str(e)}", exc_info=True)
            xray_recorder.add_annotation("error", str(e))
            xray_recorder.end_segment()

            return {
                "statusCode": 500,
                "body": json.dumps({"error": str(e)})
            }


HANDLER = Processor()


def lambda_handler(event, context):
    """
    AWS Lambda handler function.
    """
    return HANDLER.lambda_handler(event=event, context=context)
