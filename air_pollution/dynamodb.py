import boto3
import json
from boto3.dynamodb.conditions import Attr

# Connect to DynamoDB
dynamodb = boto3.resource('dynamodb', region_name='us-east-1')

# Specify the table name
table = dynamodb.Table('ttn_aws_db')


def get_all_items():
    """Fetch all items from the DynamoDB table with pagination."""
    items = []
    response = table.scan()
    items.extend(response.get('Items', []))

    # Continue scanning if there are more pages
    while 'LastEvaluatedKey' in response:
        response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
        items.extend(response.get('Items', []))

    return items


def get_device_data(device_id):
    """Fetch data for a specific device ID with pagination."""
    items = []
    response = table.scan(
        FilterExpression=Attr('device_id').eq(device_id)
    )
    items.extend(response.get('Items', []))

    # Continue scanning if there are more pages
    while 'LastEvaluatedKey' in response:
        response = table.scan(
            ExclusiveStartKey=response['LastEvaluatedKey'],
            FilterExpression=Attr('device_id').eq(device_id)
        )
        items.extend(response.get('Items', []))

    return items


def add_item(device_id, received_at, payload):
    """Add a new item to the table."""
    item = {
        'device_id': device_id,
        'received_at': received_at,
        'payload': json.dumps(payload),  # Convert payload to JSON string
    }
    table.put_item(Item=item)


def parse_payload(payload):
    """Parse the payload into a dictionary."""
    if isinstance(payload, str):
        try:
            # Parse the JSON string
            return json.loads(payload)
        except json.JSONDecodeError as e:
            raise ValueError(f"Error decoding JSON: {payload}") from e
    elif isinstance(payload, (dict, list)):
        # If it's already a dictionary or list, return it as is
        return payload
    else:
        raise TypeError(f"Unsupported payload type: {type(payload)}. Payload: {payload}")
