import json
import urllib.parse
import boto3
import requests
import os

print('Loading function')

s3 = boto3.client('s3')

def lambda_handler(event, context):
    project = os.environ['PRODUCT_UID']
    device = os.environ['DEVICE_UID']
    url = f"https://api.notefile.net/?product={project}&device={device}"
    headers = {"X-SESSION-TOKEN": os.environ['SESSION_TOKEN']}

    # print("Received event: " + json.dumps(event, indent=2))

    # Get the object from the event and show its content type
    s3Record = event['Records'][0]['s3']
    bucket = s3Record['bucket']['name']
    key = urllib.parse.unquote_plus(s3Record['object']['key'], encoding='utf-8')
    size = s3Record['object']['size']

    print(f"Received file with name '{key}' ({size} bytes) from bucket '{bucket}'")
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        if(response['ContentType'] == 'text/x-python-script'):
            print('Content type is valid. Sending notification to Notehub.io...')

            # Send request to Notehub API
            req = {"req": "note.add"}
            req["file"] = "file-update.qi"
            req["body"] = {"name": key, "size": size}

            rsp = requests.post(url, headers=headers, json=req)
            print(f"{rsp.status_code}: '{rsp.json()}'")

            return response['ContentType']
        else:
            print("Unsupported content type. Aborting...")
    except Exception as e:
        print(e)
        print('Error getting object {} from bucket {}. Make sure they exist and your bucket is in the same region as this function.'.format(key, bucket))
        raise e
