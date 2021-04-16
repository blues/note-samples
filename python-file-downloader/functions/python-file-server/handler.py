import boto3
import json
import os
import base64
import math
import zlib

print('Loading function')

s3 = boto3.client('s3')

def respond(err, res=None):
    return {
        'statusCode': '400' if err else '200',
        'body': { 'message': err } if err else json.dumps(res),
        'headers': {
            'Content-Type': 'application/json',
        },
    }


def delete_file(bucket, key):
    print("DELETING...")
    delResponse = s3.delete_object(Bucket=bucket, Key=key)

    if (delResponse['ResponseMetadata']['HTTPStatusCode'] == 204):
        print("Deleted")
    else:
        print("File not deleted. Please perform manual delete.")


def lambda_handler(event, context):
    # print("Received event: " + json.dumps(event, indent=2))

    bucket = "file-updater-bucket"
    operation = event['httpMethod']
    chunk_size = 250

    if operation == "GET":
        if 'queryStringParameters' in event:
            payload = event['queryStringParameters']

            if payload:
                file = payload['file']
                chunk_num = int(payload.get("chunk", 1))

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
                        fileString = base64.b64encode(response['Body'].read())

                        respBody["payload"] = fileString.decode("UTF-8")
                        respBody["crc32"] = zlib.crc32(fileString)
                        respBody["chunk_num"] = chunk_num
                        respBody["total_chunks"] = 1

                        # Uncomment to delete the file after transfer
                        # delete_file(bucket, file)
                    else:
                        # calculate number of chunks and return a substring of
                        # the requested chunk
                        chunk_offset = chunk_num - 1
                        leftover, total_chunks = math.modf(file_size/chunk_size)
                        if leftover > 0:
                            total_chunks = total_chunks+1

                        if (chunk_num > total_chunks):
                            print("Invalid chunk number..")

                            return respond('Invalid Chunk Number Requested')

                        print(f"Sending chunk {chunk_num} of {total_chunks}...")

                        fileString = response['Body'].read()
                        chunkString = fileString[chunk_offset * chunk_size:chunk_size - 1 + (chunk_size * chunk_offset)]

                        rspString = base64.b64encode(chunkString)
                        respBody["payload"] = rspString.decode("UTF-8")
                        respBody["crc32"] = zlib.crc32(rspString)
                        respBody["chunk_num"] = chunk_num
                        respBody["total_chunks"] = total_chunks

                        # Uncomment to delete the file after transfer
                        # if chunk_num == total_chunks:
                            # delete_file(bucket, file)

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
