from tests.test_hello_world import HelloWorldLambdaTestCase


class TestSuccess(HelloWorldLambdaTestCase):

    def test_success(self):
        expected_response = {
            "statusCode": 200,
            "message": "Hello from Lambda"
        }
        response = self.HANDLER.handle_request(dict(), dict())
        self.assertEqual(response, expected_response)
