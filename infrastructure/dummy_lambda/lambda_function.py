def lambda_handler(event, context):
    print("Dummy lambda executed")
    return {
        'statusCode': 200,
        'body': 'Hello from Dummy Lambda'
    }
