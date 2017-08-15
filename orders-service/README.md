# orders-service microservice
A really really simple mock microservice in which a user can register orders and mark them as completed.

## Configuration

Environment variables that should be set to configure the app are:
 - `DYNAMODB_ENDPOINT` - default: `localhost:8000`
 - `REGION_NAME` - default: `eu-west-1`

## API endpoints

`/order` -- methods `GET` `POST`
 - `GET` - retrieves all orders as json.
 - `POST` - puts a new order in the database. requires json with the following:
      ```json
       {
        "customer": "customer's username",
        "vendor": "vendor's username",
        "items": ["coffee", "chocolate muffin", 789123, 467832]
      }
      ```
      The order will automatically be assigned a UID. All items are converted to strings upon receipt.


`/order/<uid>` -- methods `GET` `PUT`
 - `GET` - retrieves info about the particular order.
 - `PUT` - Allows the order to be marked as complete. The following json must be posted:
      ```json
      {
        "completed": "True",
      }
      ```
      The completion date will be automatically recorded.
