package com.example;

import com.amazonaws.services.dynamodbv2.AmazonDynamoDB;
import com.amazonaws.services.dynamodbv2.AmazonDynamoDBClientBuilder;
import com.amazonaws.services.dynamodbv2.document.DynamoDB;
import com.amazonaws.services.dynamodbv2.document.Table;
import com.amazonaws.services.dynamodbv2.document.Item;
import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import software.amazon.awssdk.http.HttpResponse;
import software.amazon.awssdk.http.apache.ApacheHttpClient;
import software.amazon.awssdk.services.dynamodb.model.AttributeValue;
import software.amazon.awssdk.services.dynamodb.DynamoDbClient;

import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse.BodyHandlers;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import org.json.JSONObject;

public class Processor implements RequestHandler<Map<String, Object>, String> {

    private static final String WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast?latitude=52.52&longitude=13.41&current=temperature_2m,wind_speed_10m&hourly=temperature_2m,relative_humidity_2m,wind_speed_10m";
    private static final String DYNAMO_TABLE = System.getenv("TARGET_TABLE");

    @Override
    public String handleRequest(Map<String, Object> input, Context context) {
        try {
            // Fetch weather data
            HttpClient client = HttpClient.newHttpClient();
            HttpRequest request = HttpRequest.newBuilder()
                    .uri(URI.create(WEATHER_API_URL))
                    .GET()
                    .build();
            HttpResponse<String> response = client.send(request, BodyHandlers.ofString());
            JSONObject json = new JSONObject(response.body());

            // Extract relevant fields
            JSONObject forecast = json.getJSONObject("hourly");
            JSONObject hourlyUnits = json.getJSONObject("hourly_units");

            // Generate UUID
            String id = UUID.randomUUID().toString();

            // Save to DynamoDB
            AmazonDynamoDB dynamoDBClient = AmazonDynamoDBClientBuilder.defaultClient();
            DynamoDB dynamoDB = new DynamoDB(dynamoDBClient);
            Table table = dynamoDB.getTable(DYNAMO_TABLE);

            Item item = new Item()
                    .withPrimaryKey("id", id)
                    .withJSON("forecast", forecast.toString());

            table.putItem(item);

            return "Weather data saved successfully with ID: " + id;

        } catch (Exception e) {
            e.printStackTrace();
            return "Error fetching/storing weather data: " + e.getMessage();
        }
    }
}
