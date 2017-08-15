from __future__ import print_function # Python 2/3 compatibility
from flask import Flask, Response
import datetime
import uuid
import os

application = Flask(__name__, static_url_path="")
app = application


#---------------- Conecting to, or creating the database table ----------------
import boto3
import botocore
from botocore.exceptions import ClientError

DYNAMODB_ENDPOINT = os.environ.get('DYNAMODB_ENDPOINT', "http://localhost:8000")
REGION_NAME = os.environ.get('REGION_NAME', "eu-west-1")
dynamodb = boto3.resource('dynamodb', region_name=REGION_NAME, endpoint_url=DYNAMODB_ENDPOINT)

ORDERS_TABLE_NAME = "orders"
try:
    print("Attempting to fetch " + ORDERS_TABLE_NAME + " table.")
    orders_table = dynamodb.Table(ORDERS_TABLE_NAME)
    print(ORDERS_TABLE_NAME + " table status: ", orders_table.table_status)
except ClientError as ce:
    if ce.response['Error']['Code'] == 'ResourceNotFoundException':
        print("Table " + ORDERS_TABLE_NAME + " does not exist. Creating it now.")
        try:
            orders_table = dynamodb.create_table(
                TableName=ORDERS_TABLE_NAME,
                KeySchema=[
                    {
                        'AttributeName': 'order',
                        'KeyType': 'HASH'  #Partition key
                    },
                ],
                AttributeDefinitions=[
                    {
                        'AttributeName': 'order',
                        'AttributeType': 'S'
                    },
                ],
                ProvisionedThroughput={
                    'ReadCapacityUnits': 10,
                    'WriteCapacityUnits': 10
                }
            )

            dynamodb.meta.client.get_waiter('table_exists').wait(TableName=ORDERS_TABLE_NAME)
            print("Table " + ORDERS_TABLE_NAME + " has been created.")
            print(ORDERS_TABLE_NAME + " table status:", orders_table.table_status)
        except Exception as e:
            raise e

    else:
        print("Unknown exception occurred while querying for the " + ORDERS_TABLE_NAME + " table. Printing full error:")
        raise ce





#---------------- Defining the API endpoints ----------------
from flask_restful import Resource, Api

api = Api(app)

class OrdersApi(Resource):
    def get(self, order_id):
        try:
            order = orders_table.get_item(
                Key={
                    'order': order_id,
                }
            )

            return order["Item"], 200
        except Exception as e:
            return {'error': 'order ' + order_id + 'could not be found.'}, 404

    def put(self, order_id):
        complete = request.json.get('complete', None)
        complete = (complete in ['true', 'True'])

        if complete is None or not complete:
            return {'error': 'a property \'complete\' is required, and must be of value True'}, 400

        try:
            orders_table.update_item(
                Key={
                    'order': order_id,
                },
                UpdateExpression='SET complete = :comp, complete_date_time = :datetime',
                ExpressionAttributeValues={
                    ':comp': True,
                    ':datetime': datetime.datetime.utcnow().isoformat()
                }
            )
        except Exception as e:
            raise


        try:
            order = orders_table.get_item(
                Key={
                    'order': order_id,
                }
            )
        except Exception as e:
            raise

        return order["Item"], 200

class AllOrders(Resource):
    def get(self):
        try:
            orders = orders_table.scan()

            return orders['Items'], 200
        except Exception as e:
            return {'error': 'error fetching order.'}, 404

    def post(self):
        customer = request.json.get('customer', None)
        vendor = request.json.get('vendor', None)
        items = request.json.get('items', None)
        items  = [str(a) for a in items] #mapping all of the items to strings

        order_id = uuid.uuid4().hex

        if customer is None:
            return {'error': 'customer is a required property for this put.'}, 400
        if vendor is None:
            return {'error': 'vendor is a required property for this put.'}, 400
        if items is None:
            return {'error': 'items is a required property for this put.'}, 400
        elif not isinstance(items, list):
            return {'error': 'items must be a list of strings'}, 400

        try:
            orders_table.put_item(Item={
                        'order': order_id,
                        'customer': customer,
                        'vendor': vendor,
                        'items': items,
                        'complete': False,
                        'created': datetime.datetime.utcnow().isoformat()
                    })
        except Exception as e:
            raise


        try:
            order = orders_table.get_item(
                Key={
                    'order': order_id,
                }
            )
        except Exception as e:
            raise

        return order["Item"], 200


api.add_resource(OrdersApi, '/order/<string:order_id>')
api.add_resource(AllOrders, '/order')


if __name__ == '__main__':
    app.run(host="0.0.0.0",port=os.environ.get('PORT', 5000),debug=True)
