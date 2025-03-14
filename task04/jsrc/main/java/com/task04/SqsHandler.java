package com.task04;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import com.syndicate.deployment.annotations.lambda.LambdaHandler;
import com.syndicate.deployment.model.RetentionSetting;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

@LambdaHandler(
		lambdaName = "sqs_handler",
		roleName = "sqs_handler-role",
		isPublishVersion = true,
		aliasName = "${lambdas_alias_name}",
		logsExpiration = RetentionSetting.SYNDICATE_ALIASES_SPECIFIED
)
public class SqsHandler implements RequestHandler<Map<String, Object>, Map<String, Object>> {

	public Map<String, Object> handleRequest(Map<String, Object> event, Context context) {
		System.out.println("Received SQS event: " + event);

		// Extract messages
		if (event.containsKey("Records")) {
			List<Map<String, Object>> records = (List<Map<String, Object>>) event.get("Records");
			for (Map<String, Object> record : records) {
				String messageBody = (String) record.get("body");
				System.out.println("SQS Message: " + messageBody);
			}
		}

		Map<String, Object> resultMap = new HashMap<>();
		resultMap.put("statusCode", 200);
		resultMap.put("body", "SQS Message Processed");
		return resultMap;
	}
}
