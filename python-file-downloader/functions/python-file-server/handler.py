import boto3
import json
import os
import base64

print('Loading function')

s3 = boto3.client('s3')

def respond(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': err if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        },
    }


def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))

    bucket = "file-updater-bucket"
    operation = event['httpMethod']
    chunk_size = 4000

    if operation == "GET":
        if 'queryStringParameters' in event:
            payload = event['queryStringParameters']

            if payload:
                file = payload['file']
                chunk_num = payload.get("chunk", 0)

                print(f"Fetching File '{file}'...")

                response = s3.get_object(Bucket=bucket, Key=file)
                # print(response)

                if response['ContentType'] == 'text/x-python-script':
                    print('Content type is valid. Returning file payload to client...')

                    # Determine if the file is large enough to be sent in one-shot, or
                    # if it needs to be chunked.
                    file_size = response["ContentLength"]
                    respBody = {"payload": ""}

                    if file_size < chunk_size:
                        print('Sending Single Chunk...')

                        # Base64 Encode the file and return
                        fileString = base64.b64encode(response['Body'].read()).decode("UTF-8")

                        respBody["payload"] = fileString
                    else:
                        # calculate number of chunks and return
                        total_chunks = 0
                        print(f"Sending chunk {chunk_num} of {total_chunks}...")

                    return respond(None, respBody)

                else:
                    print("Unsupported content type. Aborting...")

                    return respond('Invalid File Type')
            else:
                print("No file provided. Aborting...")

                return respond('No file name provided')
        else:
            print("No query string values provided. Aborting...")

            return respond('No query string values provided')
    else:
        return respond('Unsupported method "{}"'.format(operation))
