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

            # Generate a unique ID
            item_id = str(uuid.uuid4())

            # Format data to match DynamoDB schema
            item = {
                "id": item_id,
                "forecast": {
                    "elevation": weather_data.get("elevation", 0),
                    "generationtime_ms": weather_data.get("generationtime_ms", 0),
                    "hourly": {
                        "temperature_2m": [{"N": str(temp)} for temp in weather_data["hourly"].get("temperature_2m", [])],
                        "time": [{"S": t} for t in weather_data["hourly"].get("time", [])]
                    },
                    "hourly_units": {
                        "temperature_2m": {"S": weather_data["hourly_units"].get("temperature_2m", "°C")},
                        "time": {"S": weather_data["hourly_units"].get("time", "ISO8601")}
                    },
                    "latitude": {"N": str(weather_data.get("latitude", 0))},
                    "longitude": {"N": str(weather_data.get("longitude", 0))},
                    "timezone": {"S": weather_data.get("timezone", "")},
                    "timezone_abbreviation": {"S": weather_data.get("timezone_abbreviation", "")},
                    "utc_offset_seconds": {"N": str(weather_data.get("utc_offset_seconds", 0))}
                }
            }

            # Store the data in DynamoDB
            put_response = table.put_item(Item=item)

            # Log DynamoDB response
            _LOG.info(f"DynamoDB PutItem Response: {put_response}")
            _LOG.info(f"Inserted Item: {json.dumps(item, indent=2)}")

            # Ensure DynamoDB write was successful
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
