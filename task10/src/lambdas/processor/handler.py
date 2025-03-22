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

# Environment variable for the DynamoDB table name
DYNAMODB_TABLE = os.getenv("target_table", "Weather")

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

        _LOG.info("Fetching weather data from Open-Meteo API")
        xray_recorder.begin_segment("WeatherLambdaFunction")

        try:
            # Fetch weather data from Open-Meteo API
            response = requests.get(WEATHER_API_URL)
            response.raise_for_status()
            weather_data = response.json()

            # Format data to match the required schema
            item = {
                "id": str(uuid.uuid4()),  # Generate unique ID
                "forecast": {
                    "elevation": weather_data.get("elevation", 0),
                    "generationtime_ms": weather_data.get("generationtime_ms", 0),
                    "hourly": {
                        "temperature_2m": weather_data["hourly"].get("temperature_2m", []),
                        "time": weather_data["hourly"].get("time", [])
                    },
                    "hourly_units": {
                        "temperature_2m": weather_data["hourly_units"].get("temperature_2m", "C"),
                        "time": weather_data["hourly_units"].get("time", "ISO8601")
                    },
                    "latitude": weather_data.get("latitude", 0),
                    "longitude": weather_data.get("longitude", 0),
                    "timezone": weather_data.get("timezone", ""),
                    "timezone_abbreviation": weather_data.get("timezone_abbreviation", ""),
                    "utc_offset_seconds": weather_data.get("utc_offset_seconds", 0)
                }
            }

            # Store the data in DynamoDB
            table.put_item(Item=item)
            _LOG.info("Weather data stored successfully in DynamoDB")

            xray_recorder.end_segment()

            return {
                "statusCode": 200,
                "body": json.dumps({"message": "Weather data stored successfully!"})
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
