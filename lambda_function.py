import json
import boto3
import uuid

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Orders')               #update your DDB table name

def lambda_handler(event, context):
    try:
        # Log the entire event for debugging
        print("Event:", event)
        
        if event['body'] is None:
            raise ValueError("Request body is empty")
        
        # Parse the JSON body of the incoming request
        body = json.loads(event['body'])
        print("Parsed body:", body)  # Add this line to log the parsed body
        
        process_order(body)
        send_notification(body)
        store_order_in_dynamodb(body)
        
        return {
            'statusCode': 200,
            'body': json.dumps('Messages processed successfully')
        }
    except Exception as e:
        print(f"Error: {e}")
        return {
            'statusCode': 500,
            'body': json.dumps(f'Internal Server Error: {str(e)}')
        }

def process_order(order):
    print(f"Processing order: {order}")
    sqs = boto3.client('sqs')
    response = sqs.send_message(
        QueueUrl='https://sqs.YOUR_REGION.amazonaws.com/YOUR_ACCOUNT_ID/MyProcessingQ.fifo',  # Update with your SQS queue URL
        MessageBody=json.dumps(order),
        MessageGroupId='Group1',  # Ensure MessageGroupId is specified for FIFO queues
        MessageDeduplicationId=str(uuid.uuid4())  # Generate a unique MessageDeduplicationId
    )
    print(f"Message sent to SQS FIFO queue: {response}")

def send_notification(order):
    sns = boto3.client('sns')
    response = sns.publish(
        TopicArn='arn:aws:sns:YOUR_REGION:YOUR_ACCOUNT_ID:OrderNotification',  # Update with your SNS topic ARN
        Message=json.dumps(order),
        Subject='Order Shipped'
    )
    print(f"Notification sent for order: {order}")

def store_order_in_dynamodb(order):
    # Ensure orderID is present in the order
    if 'orderID' not in order:
        raise ValueError("Missing orderID in the order")
        
    item = {
        'OrderID': order['orderID'], 
        'customerName': order['customerName'],
        'items': json.dumps(order['items']),
        'shippingAddress': order['shippingAddress']
    }
    response = table.put_item(Item=item)
    print(f"Order stored in DynamoDB: {response}")