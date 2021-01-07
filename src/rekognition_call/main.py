# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.

# Permission is hereby granted, free of charge, to any person obtaining a copy of
# this software and associated documentation files (the "Software"), to deal in
# the Software without restriction, including without limitation the rights to
# use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of
# the Software, and to permit persons to whom the Software is furnished to do so.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS
# FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER
# IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

import boto3
import os

region = os.getenv('AWS_REGION')
sns_topic_arn = os.getenv('SNS_TOPIC_ARN')
role_arn = os.getenv('IAM_ROLE_ARN')
# the following env vars control where to look for text, with each value from 0 to 1
text_search_left = float(os.getenv('TEXT_SEARCH_LEFT', '0.2'))
text_search_top = float(os.getenv('TEXT_SEARCH_TOP', '0.8'))
text_search_width = float(os.getenv('TEXT_SEARCH_WIDTH', '0.7'))
text_search_height = float(os.getenv('TEXT_SEARCH_HEIGHT', '0.15'))
min_confidence = float(os.getenv('MIN_WORD_DETECT_CONFIDENCE', '90'))


def is_video_file(object_key):
    valid_video_extensions = {'.mp4', '.mov', '.avi'}
    _, file_extension = os.path.splitext(object_key)
    return file_extension.lower() in valid_video_extensions


def send_video_file_to_rekognition(bucket_name, object_key):
    print(f'Sending the following to Rek: bucket {bucket_name} object {object_key} in region {region}')
    print(f'Using IAM role {role_arn} and SNS topic {sns_topic_arn}')

    rek = boto3.client('rekognition', region_name=region)
    response = rek.start_text_detection(
        Video={'S3Object': {'Bucket': bucket_name, 'Name': object_key}},
        NotificationChannel={'RoleArn': role_arn, 'SNSTopicArn': sns_topic_arn},
        Filters={
            "WordFilter": {"MinConfidence": min_confidence},
            "RegionsOfInterest": [{
                "BoundingBox": {
                    "Width": text_search_width,
                    "Height": text_search_height,
                    "Left": text_search_left,
                    "Top": text_search_top
                }
            }]
        })
    startJobId = response['JobId']
    print(f'Rekognition start_text_detection launched.  Job Id: {startJobId}')


def lambda_handler(event, context):
    print(f'In lambda for rek_call.  Event is {event}')
    # see https://docs.aws.amazon.com/lambda/latest/dg/with-s3.html for info about event object
    for record in event['Records']:
        s3_info = record['s3']
        object_key = s3_info['object']['key']
        bucket_name = s3_info['bucket']['name']
        if is_video_file(object_key):
            send_video_file_to_rekognition(bucket_name, object_key)
