from commons.log_helper import get_logger
from commons.abstract_lambda import AbstractLambda

_LOG = get_logger(__name__)


class HelloWorld(AbstractLambda):

    def validate_request(self, event) -> dict:
        """
        This method can be used to validate incoming requests.
        Currently, it's not implemented.
        """
        pass

    def handle_request(self, event, context):
        """
        This method handles the incoming request event.
        Currently, it returns a fixed HTTP 200 response.
        """
        # todo: implement business logic here
        _LOG.info("Handling request with event: %s", event)

        response = {
            "statusCode": 200,
            "body": '{"message": "Hello, World!"}'
        }
        return response


HANDLER = HelloWorld()


def lambda_handler(event, context):
    """
    AWS Lambda's entry point.
    This function delegates the processing to the AbstractLambda.
    """
    return HANDLER.lambda_handler(event=event, context=context)
