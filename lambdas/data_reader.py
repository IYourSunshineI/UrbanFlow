import json

def lambda_handler(event, context):
    print("Hello from UrbanFlowDataReader!")
    print("Received event:", json.dumps(event))
    
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps({
            'message': 'Hello from UrbanFlow Data Reader!',
            'input_event': event
        })
    }
