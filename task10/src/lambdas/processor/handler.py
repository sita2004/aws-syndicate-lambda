import uuid
import requests
import boto3
from aws_xray_sdk.core import xray_recorder
from aws_xray_sdk.core import patch_all
from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda

_LOG = get_logger(__name__)
patch_all()  # Enable X-Ray tracing for AWS service calls

# DynamoDB configuration
dynamodb = boto3.resource('dynamodb')
table_name = "Weather"  # Will be replaced with alias during deployment


class Processor(AbstractLambda):
    def __init__(self):
        super().__init__()
        self.table = dynamodb.Table(table_name)

    def validate_request(self, event) -> dict:
        """Validate the incoming event."""
        # Example: Add validation for GET request if needed
        if "httpMethod" in event and event["httpMethod"] != "GET":
            raise ValueError("Invalid request method. Only GET is allowed.")
        return event  # Return the validated event if no error occurs

    @xray_recorder.capture("handle_request")  # Enable tracing for this method
    def handle_request(self, event, context):
        """
        Handles the incoming event for weather data processing.
        Retrieves weather data from Open-Meteo API and stores it in DynamoDB.
        """
        try:
            # Fetch weather data from Open-Meteo API
            response = requests.get(
                "https://api.open-meteo.com/v1/forecast?"
                "latitude=52.52&longitude=13.41&current=temperature_2m,wind_speed_10m&"
                "hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"
            )
            response.raise_for_status()  # Raise an error for bad responses
            forecast_data = response.json()

            # Prepare DynamoDB item based on the schema
            weather_item = {
                "id": str(uuid.uuid4()),
                "forecast": {
                    "elevation": forecast_data.get("elevation"),
                    "generationtime_ms": forecast_data.get("generationtime_ms"),
                    "hourly": {
                        "temperature_2m": forecast_data["hourly"]["temperature_2m"],
                        "time": forecast_data["hourly"]["time"]
                    },
                    "hourly_units": {
                        "temperature_2m": forecast_data["hourly_units"]["temperature_2m"],
                        "time": forecast_data["hourly_units"]["time"]
                    },
                    "latitude": forecast_data.get("latitude"),
                    "longitude": forecast_data.get("longitude"),
                    "timezone": forecast_data.get("timezone"),
                    "timezone_abbreviation": forecast_data.get("timezone_abbreviation"),
                    "utc_offset_seconds": forecast_data.get("utc_offset_seconds")
                },
            }

            # Insert the item into DynamoDB
            self.table.put_item(Item=weather_item)
            _LOG.info(f"Successfully saved weather data to DynamoDB: {weather_item}")

            return {
                "statusCode": 200,
                "body": "Weather data has been successfully saved."
            }

        except Exception as e:
            _LOG.error(f"Error processing weather data: {e}")
            return {
                "statusCode": 500,
                "body": "An error occurred while processing the request."
            }


HANDLER = Processor()


def lambda_handler(event, context):
    return HANDLER.lambda_handler(event=event, context=context)