"""Remove all objects from bucket before deleting bucket in CloudFormation stack (otherwise bucket deletion fails)

When CloudFormation delete-stack is triggered, and bucket contains objects, the stack deletion will fail. This Custom
Resource will remove objects from bucket so that the bucket can be cleanly deleted with the stack.
"""
import boto3
import logging
from crhelper import CfnResource


helper = CfnResource(json_logging=False, log_level='DEBUG', boto_level='CRITICAL')


def handler(event: dict, context: dict) -> None:
    """AWS Lambda function handler

    :type: dict
    :param: event: aws cloudformation custom resource event

    :type: dict
    :param: context: aws lambda function environment context

    :rtype: dict
    """
    logger: logging.Logger = log('CUSTOM RESOURCE HANDLER')
    logger.info(f'EVENT: {event}')
    helper(event, context)


@helper.create
def create(event: dict, _) -> None:
    """Custom Resource Helper for CloudFormation Create Event.
    Decorator abstracts away the HTTP request/response cycle handled during Custom Resource events

    Example Purpose: Populates empty bucket with 1000+ objects to specifically illustrate the CFn Delete event

    :type: dict
    :param: event: aws cloudformation custom resource event

    :rtype: None
    """
    logger: logging.Logger = log('CUSTOM RESOURCE HANDLER: CREATE')

    # NOTE: Code below is for example purposes only, and would not be desirable in practical usage of the custom resource
    client = boto3.client('s3')

    for i in range(1001):
        client.put_object(
            Bucket=event['ResourceProperties']['BucketName'],
            Body=b'Foo',
            Key='file_' + '{:04d}'.format(i)
        )
    logger.info('Successfully put objects in bucket')


@helper.update
def update(event: dict, _) -> None:
    """Custom Resource Helper for CloudFormation Update Event.
    Decorator abstracts away the HTTP request/response cycle handled during Custom Resource events

    Example Purpose: Populates empty bucket with 1000+ objects (if objects not present) to specifically illustrate the CFn Delete event

    :type: dict
    :param: event: aws cloudformation custom resource event

    :rtype: None
    """
    logger: logging.Logger = log('CUSTOM RESOURCE HANDLER: UPDATE')

    # NOTE: Code below is for example purposes only, and would not be desirable in practical usage of the custom resource
    client = boto3.client('s3')
    bucket_name = event['ResourceProperties']['BucketName']
    objects = client.list_objects_v2(Bucket=bucket_name)
    if objects['KeyCount'] < 1000:
        create(event)
    else:
        logger.info('Bucket has already been populated.')


@helper.delete
def delete(event: dict, _) -> None:
    """Custom Resource Helper for CloudFormation Delete Event.
    Decorator abstracts away the HTTP request/response cycle handled during Custom Resource events

    Example Purpose: Removes all objects from bucket, allowing the bucket to be removed during a CFn Stack Deletion
    Note: If this process is not facilitated, the Stack Deletion fails because the S3 bucket has objects within.

    :type: dict
    :param: event: aws cloudformation custom resource event

    :rtype: None
    """
    logger: logging.Logger = log('CUSTOM RESOURCE HANDLER: DELETE')
    s3 = boto3.resource('s3')
    bucket_name = event['ResourceProperties']['BucketName']
    bucket = s3.Bucket(bucket_name)
    objects = bucket.objects.all()
    objects.delete()

    logger.info('Successfully deleted all objects in bucket')


def log(name: str = 'aws_entity', logging_level: str = logging.INFO) -> logging.Logger:
    """Instantiate a logger
    """
    logger: logging.Logger = logging.getLogger(name)
    log_handler: logging.StreamHandler = logging.StreamHandler()
    formatter: logging.Formatter = logging.Formatter('%(levelname)-8s %(asctime)s %(name)-12s %(message)s')
    log_handler.setFormatter(formatter)
    logger.addHandler(log_handler)
    logger.setLevel(logging_level)
    return logger
