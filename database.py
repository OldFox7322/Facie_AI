import boto3
import uuid
import json
import logging
import os
from botocore.exceptions import ClientError
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

load_dotenv()
AWS_REGION = "eu-north-1"

# Initialize DynamoDB resource
dynamo_db = boto3.resource(
    "dynamodb",
    region_name=AWS_REGION
)

TABLE_NAME = os.getenv('TABLE_NAME')
dynamo_db = boto3.resource("dynamodb")
table = dynamo_db.Table(TABLE_NAME)
S3_BUCKET_NAME = os.getenv('S3_BUCKET_NAME')
S3_FOLDER = os.getenv('S3_FOLDER')

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


# ============================
# Upload file to AWS S3 bucket
# ============================
def upload_file_to_s3(file_content: bytes, s3_key: str, content_type: str) -> Optional[str]:
    """
    Uploads a file (photo) to the S3 bucket using a given S3 key.
    Returns the public URL of the uploaded file or None on failure.
    """
    try:
        s3_client = boto3.client('s3', region_name='eu-north-1')
        s3_client.put_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key,
            Body=file_content,
            ContentType=content_type
        )
        return f'https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{s3_key}'
    except Exception as e:
        logging.error(f'Error uploading file to S3 at {s3_key}: {e}')
        return None


# ======================================
# Retrieve a photo file from AWS S3 by key
# ======================================
def get_file_from_s3(s3_key: str) -> Optional[bytes]:
    """
    Retrieves a file (photo) from S3 by its S3 key.
    Returns the file bytes or None if the file is not found or on error.
    """
    try:
        s3_client = boto3.client('s3', region_name=AWS_REGION)
        response = s3_client.get_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key
        )
        file_content = response['Body'].read()        
        return file_content
    except ClientError as e: 
        if e.response['Error']['Code'] == 'NoSuchKey':
            logging.error(f'S3 file not found for key: {s3_key}')
            return None
        logging.error(f'S3 file not found for key: {s3_key}')
        return None
    except Exception as e:
        logging.error(f'Error reading file from S3 at {s3_key}: {e}')
        return None


# ======================================
# Create a new friend record in DynamoDB
# ======================================
def create_new_friend(
    data: Dict[str, Any],
    filename: str
    ) -> Dict[str, Any]:
    """
    Creates a new record (friend) in DynamoDB and constructs S3 file metadata.
    Generates a UUID for the friend and stores S3 URL.
    """
    s3_client = boto3.client('s3', region_name=AWS_REGION)

    friend_id = str(uuid.uuid4())
    s3_key = f'{S3_FOLDER}/{friend_id}/{filename}'
    photo_url = f'https://{S3_BUCKET_NAME}.s3.{AWS_REGION}.amazonaws.com/{s3_key}'

    item: Dict[str, Any] = {
        'FriendID': friend_id,
        'Name': data['Name'],
        'Profession': data['Profession'],
        'ProfessionDescription': data['ProfessionDescription'],
        'S3Key': s3_key,
        'PhotoUrl': photo_url
    }

    try:
        table.put_item(Item=item)
        return item
    except Exception as e:
        logging.error(f'DynamoDB error when creating record: {e}')
        return None


# =====================================
# Retrieve one friend record by FriendID
# =====================================
def get_one_friend(friend_id: str) -> Optional[Dict[str, Any]]:
    """
    Fetches one friend record from DynamoDB by FriendID.
    Returns the record dict or None if not found.
    """
    try:
        response = table.get_item(Key={'FriendID': friend_id})
        return response.get('Item')
    except Exception as e:
        logging.error(f'DynamoDB error reading record: {e}')
        return None


# ======================================
# Retrieve all friends from DynamoDB table
# ======================================
def get_all_friends() -> Optional[List[Dict[str, Any]]]:
    """
    Scans the entire DynamoDB table to retrieve all friends.
    Handles pagination using LastEvaluatedKey.
    """
    try:
        response = table.scan()
        items = response.get('Items', [])
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response.get('Items', []))
        logging.info(f"Successfully retrieved {len(items)} friends.")
        return items
    except Exception as e:
        logging.error(f'DynamoDB error during full table scan: {e}')
        return None


# ======================================
# Delete a friend record from DynamoDB
# ======================================
def delete_friend(friend_id: str):
    """
    Deletes a friend record from DynamoDB by FriendID.
    Returns True on success, False otherwise.
    """
    try:
        response = table.delete_item(Key={'FriendID': friend_id})
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return True
        else:
            logging.error(f"DynamoDB returned non-200 status for delete: {response}")
            return False
    except ClientError as e:
        logging.error(f"DynamoDB ClientError during delete: {e}")
        return False
    except Exception as e:
        logging.error(f"Unknown error during delete: {e}")
        return False


# ======================================
# Delete photo file from AWS S3 bucket
# ======================================
def delete_file_from_s3(s3_key: str) -> bool:
    """
    Deletes a photo file from the S3 bucket by S3 key.
    Returns True if deletion was successful, otherwise False.
    """
    try:
        s3_client = boto3.client('s3', region_name=AWS_REGION)
        
        response = s3_client.delete_object(
            Bucket=S3_BUCKET_NAME,
            Key=s3_key
        )
        
        if response['ResponseMetadata']['HTTPStatusCode'] in [200, 204]:
            logging.info(f"Successfully deleted S3 object: {s3_key}")
            return True
        else:
            logging.error(f"S3 delete failed for {s3_key} with status: {response['ResponseMetadata']['HTTPStatusCode']}")
            return False
    except ClientError as e:
        logging.error(f"S3 ClientError during delete for key {s3_key}: {e}")
        return False
    except Exception as e:
        logging.error(f"Unknown error during S3 delete: {e}")
        return False
