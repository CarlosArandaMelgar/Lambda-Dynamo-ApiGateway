import boto3
import json
import logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)
from src.custom_encoder import CustomEncoder

dynamoTableName = 'product_inventory'
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(dynamoTableName)

getMethod = 'GET'
postMethod = 'POST'
patchMethod = 'PATCH'
deleteMethod = 'DELETE'

healthPath = '/health'
productPath = '/product'
productsPath = '/products'

def lambda_handler(event, context):
     
    httpMethod = event['httpMethod']
    path = event['path']

    if httpMethod == getMethod and path == healthPath:
        response = buildResponse(200)
    elif httpMethod == getMethod and path == productPath:
        response = getProduct(event['queryStringParameters']['productId'])
    elif httpMethod == getMethod and path == productsPath:
        response = getProducts()
    elif httpMethod == postMethod and path == productPath:
        response = saveProduct(json.loads(event['body']))
    elif httpMethod == patchMethod and path == productPath:
        requestBody = json.loads(event['body'])
        response = modifyProduct(requestBody['productId'], requestBody['updateKey'], requestBody['updateValue'])
    elif httpMethod == deleteMethod and path == productPath:
        requestBody = json.loads(event['body'])
        response = deleteProduct(requestBody['productId'])
    else:
        response = buildResponse(404, 'Not Found')
    return response

def getProduct(productId):
    try:
        response = table.get_item(
            Key={
                "productId  ": productId
            }
        ) 
        if 'Item' in response:
            return buildResponse(200, response['Item'])
        else:
            return buildResponse(404, {'Message': 'ProductId: %s not found' % productId})
    except Exception as e:
        logger.exception(f'Error Desde Logger: {e}')

def getProducts():
    try:
        response = table.scan()
        result = response['Items']

        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            result.extend(response['Item'])

        body={
            'products': response
        }
        return buildResponse(200, body)
    
    except Exception as e:
        logger.exception(f'Error desde Logger: {e}')

def saveProduct(requestBody):
    try:
        table.put_item(Item=requestBody)
        body={
            'Operation': 'SAVE',
            'Message': 'SUCESS',
            'Item': requestBody
        }
        return buildResponse(200, body)
    except Exception as e:
        logger.exception(f'Error desde logger: {e}')

def modifyProduct(productId, updateKey, updateValue):
    try:
        response = table.update_item(
            Key={
                'productId  ': productId
            },
            UpdateExpression = 'set %s  = :value' % updateKey,
            ExpressionAttributeValues={
                ':value': updateValue
            },
            ReturnValues = 'UPDATED_NEW'
        ) 
        body={
            'Operation': 'UPDATE',
            'Message': 'SUCESS',
            'UpdatedAttributes': response
        }
        return buildResponse(200, body)
    except Exception as e:
        logger.exception(f'Error desde logger: {e}')

def deleteProduct(productId): 
    try:
        response = table.delete_item(
            key = {
                'productId  ': productId
            },
        ReturnValues='ALL_OLD'
        )
        body = {
            'Operation': 'DELETE',
            'Message:': 'SUCCESS',
            'deletedItem': response
        }
        return buildResponse(200, body)
    except Exception as e:
        logger.exception(f'Error desde logger: {e}')


def buildResponse(statusCode, body=None):
    response = {
        'statusCode': statusCode,
        'headers': {
            'Content-Type': 'application/json',
            'Acess-Control-Allow-Origin': '*'
        }
    }
    if body is not None:
        response['body'] = json.dumps(body, cls=CustomEncoder)  # Aquí asumimos que 'body' es un objeto Python que deseas convertir a JSON
    return response
