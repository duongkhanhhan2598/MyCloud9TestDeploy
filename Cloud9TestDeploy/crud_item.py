import boto3
def lambda_handler(event,context):
    print('HELOO WORLD')
    return{
        'body': 'HELLO'
    }