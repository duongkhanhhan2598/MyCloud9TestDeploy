import json
import boto3
import botocore
import base64
import hashlib
import hmac
from PIL import Image
import io
from boto3.dynamodb.conditions import Key, Attr
from pprint import pprint
import os
from urllib.parse import urlparse 
from urllib.parse import urlencode
import urllib3
dynamodb = boto3.resource('dynamodb',
    aws_access_key_id = 'AKIARMY6GHES4LVNARJD',
    aws_secret_access_key = '5oye3Z1YeePpGZVt+m7/ZXipJmFXnAqIdSpSaMCI'
)
table = dynamodb.Table('SampleTable') 
s3 = boto3.resource('s3',
    region_name = 'ap-northeast-1',
    aws_access_key_id = 'AKIARMY6GHESX2GD5NCP',
    aws_secret_access_key = 'P2MMx90z30Jf8DfpnVDfoQoMPm8ueYfAR9xByWVc'
)
bucket = s3.Bucket('bucket-of-han')
bucket_name = 'bucket-of-han'
#Method Part_1
getMethod = 'GET'
postMethod = 'POST'
putMethod = 'PUT'
#path func
create_res = '/create'
read_res = '/read'
update_res = '/update'
#path
itemPath = '/api/v1/user-management/users/user-id'

def lambda_handler(event,context):
    crud_from_api(event)
    
def crud_from_api(event):
    httpMethod = event['httpMethod']
    path = event['path']
    body = json.loads(event.get('body',{}))
    data = body.get('data', {})
    # validate_id(data,dynamodb)
    if httpMethod == postMethod and path == (itemPath + create_res):
        base64_of_img = data.get('image',{}).get('base64','')
        img_empty = data.get('image',{})
        #Check img empty
        if base64_of_img == '' or img_empty == '':
            data['image'] = ''
        else:
            url = decode_image_base64_to_url(data,s3)
            data['image'] = url
        #Check id existed
        if check_id_exist(data.get('id','')):
            # res = put_sample(data,dynamodb)
            res = {
                'message': 'Item Existed'
            }
            sttCode = 409
        else:
            res = put_sample(data,dynamodb)
            sttCode = 200
    elif httpMethod == putMethod and path == (itemPath + update_res):
        base64_of_img = data.get('image',{}).get('base64','')
        img_empty = data.get('image',{})
        if base64_of_img == '' or img_empty == '':
            data['image'] = ''
        else:
            url = decode_image_base64_to_url(data,s3)
            data['image'] = url
        res = update_sample(data,dynamodb)
        sttCode = 200
    elif httpMethod == getMethod and path == (itemPath + read_res):
        res = query_sample(data,dynamodb)
        sttCode = 200
    else:
        sttCode = 502
        res = 'Not Found'
    return {
        'statusCode': sttCode,
        'body': json.dumps(res)
    }
    
def check_id_exist(item,dynamodb = None):
    response = table.query(
        KeyConditionExpression = Key('id').eq(item)
    )
    for i in response['Items']:
        if item != i['id']:
            return False
        else:
            return True
#Insert, Update, Find sample
def put_sample(data, dynamodb = None):
    response = table.put_item(
        Item = {
            'id': data['id'],
            'name': data['name'],
            'phone': data['phone'],
            'address': data['address'],
            'image': data['image']
        },
    )
    return {
        'message': 'Insert Item Success',
        'data': data
    }
def update_sample(data, dynamodb = None):
    response = table.update_item(
        Key={
            'id': data['id']
        },
        UpdateExpression = "set #name = :n, #phone = :p, #address = :a, #image = :i",
        ExpressionAttributeNames= {
            '#name':'name',
            '#phone':'phone',
            '#address':'address',
            '#image':'image'
        },
        ExpressionAttributeValues = {
            ':n': data['name'],
            ':p': data['phone'],
            ':a': data['address'],
            ':i': data['image']
        },
    )
    return {
        'message': 'Update Item Success',
        "data": data
    }
def query_sample(data, dynamodb = None):
    response = table.query(
        KeyConditionExpression = Key('id').eq(data['id'])
    )
    for i in response['Items']:
        print("Item neeeee", i)
        if i.get('image', None):
            i['image'] = encode_base64_string_from_url_table(i['image'],dynamodb)
            print("image ne",i['image'])
            
        print(i['id'], ':', i['name'], '-', i['phone'], '-', i['address'], '-', i.get('image', ''))
        
        # list_item = (f"id: %s || name: %s || phone: %s || address: %s || image %s" %(str(i['id']), i['name'], i['phone'], i['address'], i['image']))
        list_item = 'id: {} || name: {} || phone: {} || address: {} || image: {}'.format(str(i['id']), str(i['name']), str(i['phone']), str(i['address']), str(i.get('image', '')))
    # list_item = response['Items']
    print('list_item=====================>', list_item)
    return {
        'message': 'Query Item Success',
        'data': list_item
    }
#Base64
def encode_base64_string_from_url_table(url_by_id,dynamodb=None):
    url_by_id_parse = urlparse(url_by_id)
    url_by_id_key = url_by_id_parse.path
    url_by_id_key = url_by_id_key[1:]
    
    response_obj = boto3.client('s3').get_object(
        Bucket = bucket_name,
        Key = url_by_id_key
    )
    url_read = response_obj['Body'].read()
    url_base64_encode = base64.b64encode(url_read)
    return url_base64_encode
def decode_image_base64_to_url(data,s3=None):
    img_name = data.get('image',{}).get('name','') + '_' + data.get('image',{}).get('date','') + '.jpeg'
    base64_string = data.get('image',{}).get('base64','')
    base64_string_decode = base64.b64decode(str(base64_string))
    img_path = ('/tmp/' + img_name)
    img = Image.open(io.BytesIO(base64_string_decode))
    img.save(img_path, 'jpeg')
    s3.Bucket(bucket_name).upload_file(img_path, img_name)
    img_location = boto3.client('s3').get_bucket_location(Bucket=bucket_name)['LocationConstraint']
    url = f"https://%s.s3.%s.amazonaws.com/%s" % (bucket_name,img_location, img_name)
    return url