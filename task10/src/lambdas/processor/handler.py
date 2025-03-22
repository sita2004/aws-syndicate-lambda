import json
import uuid
import requests
import boto3
from aws_xray_sdk.core import patch_all, xray_recorder
from aws_xray_sdk.core.models import http
from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda

_LOG = get_logger(__name__)

patch_all()  # Patch all supported libraries for X-Ray tracing

class Processor(AbstractLambda):

    def validate_request(self, event) -> dict:
        pass

    def handle_request(self, event, context):
        """
        Fetches weather forecast from Open-Meteo API and stores it in DynamoDB.
        """
        try:
            url = "https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&current=temperature_2m,wind_speed_10m&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m"
            response = requests.get(url)
            response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
            weather_data = response.json()

            item = {
                "id": str(uuid.uuid4()),
                "forecast": {
                    "elevation": weather_data.get("elevation"),
                    "generationtime_ms": weather_data.get("generationtime_ms"),
                    "hourly": {
                        "temperature_2m": weather_data.get("hourly", {}).get("temperature_2m"),
                        "time": weather_data.get("hourly", {}).get("time")
                    },
                    "hourly_units": {
                        "temperature_2m": weather_data.get("hourly_units", {}).get("temperature_2m"),
                        "time": weather_data.get("hourly_units", {}).get("time")
                    },
                    "latitude": weather_data.get("latitude"),
                    "longitude": weather_data.get("longitude"),
                    "timezone": weather_data.get("timezone"),
                    "timezone_abbreviation": weather_data.get("timezone_abbreviation"),
                    "utc_offset_seconds": weather_data.get("utc_offset_seconds")
                }
            }

            dynamodb = boto3.resource("dynamodb")
            table = dynamodb.Table("Weather") # Replace 'Weather' with your actual DynamoDB table name

            table.put_item(Item=item)
            _LOG.info(f"Weather data stored in DynamoDB: {item['id']}")

            return {
                "statusCode": 200,
                "body": json.dumps({"message": "Weather data processed and stored successfully."})
            }

        except requests.exceptions.RequestException as e:
            _LOG.error(f"Error fetching weather data: {e}")
            return {
                "statusCode": 500,
                "body": json.dumps({"error": f"Failed to fetch weather data: {e}"})
            }
        except boto3.exceptions.Boto3Error as e:
            _LOG.error(f"Error interacting with DynamoDB: {e}")
            return {
                "statusCode": 500,
                "body": json.dumps({"error": f"Failed to store data in DynamoDB: {e}"})
            }
        except Exception as e:
            _LOG.error(f"An unexpected error occurred: {e}")
            return {
                "statusCode": 500,
                "body": json.dumps({"error": f"An unexpected error occurred: {e}"})
            }

HANDLER = Processor()


def lambda_handler(event, context):
    return HANDLER.lambda_handler(event=event, context=context)
