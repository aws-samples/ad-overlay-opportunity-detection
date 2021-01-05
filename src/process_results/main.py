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
import json
from ad_placements import AdOpportunites

region = os.getenv('AWS_REGION')
min_seconds_needed = int(os.getenv('MIN_AD_DURATION_IN_SECS', '15'))
min_word_width = float(os.getenv('MIN_WORD_WIDTH', '0.05'))


def get_output_filename(filename):
    file_name, _ = os.path.splitext(filename)
    return file_name + "-results.txt"


def write_output(bucket, keyname, message):
    s3 = boto3.client('s3', region_name=region)
    s3.put_object(Body=message, Bucket=bucket, Key=keyname)


def is_word_box_large_enough(box):
    # really small words are probably incidental, and can be overlaid with an ad
    return box['Width'] >= min_word_width


def process_rek_results(rek_job_id, rek_status, video_processed):
    output_bucket = video_processed['S3Bucket']
    output_filename = get_output_filename(video_processed['S3ObjectName'])

    if rek_status != "SUCCEEDED":
        write_output(output_bucket, output_filename, f'Text detection failed: {rek_status}')
    else:
        ad_placement_finder = AdOpportunites(min_seconds_needed)

        paginationToken = ''
        finished = False
        maxResults = 100
        rek = boto3.client('rekognition', region_name=region)

        while not finished:
            response = rek.get_text_detection(JobId=rek_job_id,
                                              MaxResults=maxResults,
                                              NextToken=paginationToken)

            # we need to know the total video length to
            # check if there's an available ad slot at the end of the video
            total_video_length = response['VideoMetadata']['DurationMillis']
            ad_placement_finder.set_video_length(total_video_length)

            for textDetection in response['TextDetections']:
                text = textDetection['TextDetection']
                timestamp = int(textDetection['Timestamp'])
                found_type = str(text['Type'])
                found_string = text['DetectedText']
                bounding_box = text['Geometry']['BoundingBox']

                if found_type == "WORD":
                    print(f'Found word {found_string} at timestamp {timestamp} with width {bounding_box["Width"]} and confidence {text["Confidence"]}')
                    if is_word_box_large_enough(bounding_box):
                        ad_placement_finder.add_text_presence(timestamp)

            if 'NextToken' in response:
                paginationToken = response['NextToken']
            else:
                finished = True

        # dump out the possible ad placements
        write_output(output_bucket, output_filename, ad_placement_finder.get_available_placement_text())


def lambda_handler(event, context):
    # see https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html for info about event object
    print(f'In process_results.  Event is {event}')
    for record in event['Records']:
        body = json.loads(record['body'])
        rek_job_id = body['JobId']
        rek_status = body['Status']
        video_processed = body['Video']
        process_rek_results(rek_job_id, rek_status, video_processed)
