import os
import boto3

from botocore.exceptions import ClientError
from dotenv import load_dotenv
from loguru import logger


load_dotenv()
log_path = os.path.join(os.path.dirname(__file__), '..', 'logs', 'ingestion.log')
logger.add(log_path)

def validate_aws_credentials():
    """Validate that AWS credentials are properly configured"""
    required_vars = ['AWS_ACCESS_KEY_ID', 'AWS_SECRET_ACCESS_KEY']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise EnvironmentError(f"Missing AWS credentials: {', '.join(missing_vars)}")
        logger.error(f"Missing AWS credentials: {', '.join(missing_vars)}")

    else:
        logger.info(f"Crendentials found.")
    
    try:
        # Test the credentials
        sts = boto3.client('sts')
        identity = sts.get_caller_identity()
        logger.info(f"Authenticated as: {identity['Arn']}")
        return True
    except ClientError as e:
        logger.error(f"Invalid credentials: {e}")
        return False


if validate_aws_credentials():
    s3 = boto3.client('s3')
