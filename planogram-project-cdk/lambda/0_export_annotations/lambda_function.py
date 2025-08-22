import boto3
import os
import json
import requests
import zipfile
import tempfile
import re
from pathlib import Path
from botocore.exceptions import ClientError
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# ---- HTTP session with retry & timeout ----
HTTP_TIMEOUT = float(os.environ.get("HTTP_TIMEOUT_SECONDS", "20"))
HTTP_MAX_RETRIES = int(os.environ.get("HTTP_MAX_RETRIES", "3"))
HTTP_BACKOFF = float(os.environ.get("HTTP_BACKOFF_SECONDS", "0.5"))

def _http_session():
    s = requests.Session()
    retry = Retry(
        total=HTTP_MAX_RETRIES,
        connect=HTTP_MAX_RETRIES,
        read=HTTP_MAX_RETRIES,
        backoff_factor=HTTP_BACKOFF,
        status_forcelist=(429, 500, 502, 503, 504),
        allowed_methods=("GET", "POST"),
        raise_on_status=False,
    )
    adapter = HTTPAdapter(max_retries=retry)
    s.mount("http://", adapter)
    s.mount("https://", adapter)
    return s

_http = _http_session()

def get_label_studio_config():
    print("[get_label_studio_config] Start")
    secret_name = os.environ["LS_SECRET_NAME"]
    region = os.environ.get("AWS_REGION", "ap-southeast-1")
    print(f"[get_label_studio_config] Reading secret: {secret_name}, region: {region}")
    sm = boto3.client("secretsmanager", region_name=region)
    secret_value = sm.get_secret_value(SecretId=secret_name)
    secret = json.loads(secret_value["SecretString"])
    print(f"[get_label_studio_config] Secret loaded: keys={list(secret.keys())}")
    return secret

def get_project_s3_storage(label_studio_url, api_key, project_id):
    print(f"[get_project_s3_storage] Start for project_id={project_id}")
    headers = {'Authorization': f'Token {api_key}'}
    url = f"{label_studio_url}/api/storages/s3/?project={project_id}"
    print(f"[get_project_s3_storage] Calling URL: {url}")
    resp = _http.get(url, headers=headers, timeout=HTTP_TIMEOUT)
    resp.raise_for_status()
    data = resp.json()
    print(f"[get_project_s3_storage] Storage response: {json.dumps(data)}")
    if not data:
        print("[get_project_s3_storage] No S3 storage found!")
        raise Exception(f"No S3 storage found for project {project_id}")
    bucket = data[0]['bucket']
    prefix = data[0]['prefix'] if data[0]['prefix'] else ""
    if prefix and not prefix.endswith('/'):
        prefix += '/'
    print(f"[get_project_s3_storage] Using bucket={bucket}, prefix={prefix}")
    return bucket, prefix

def _safe_extract_all(zf: zipfile.ZipFile, dest_dir: Path):
    base = dest_dir.resolve()
    for m in zf.infolist():
        target = (dest_dir / m.filename).resolve()
        if not str(target).startswith(str(base)):
            raise Exception(f"Unsafe zip entry detected: {m.filename}")
    zf.extractall(dest_dir)

def lambda_handler(event, context):
    print(f"[lambda_handler] Event: {json.dumps(event)}")
    config = get_label_studio_config()
    project_id = event.get("project_id")
    if not project_id:
        print("[lambda_handler] ERROR: project_id missing in event")
        return {
            'statusCode': 400,
            'body': 'project_id is required in the payload'
        }
    prefix = f"annotations{project_id}"
    label_studio_url = config["LABEL_STUDIO_URL"]
    api_key = config["LS_API_KEY"]
    s3_bucket = os.environ.get('S3_BUCKET')

    # Lấy S3 prefix từ biến môi trường, mặc định là "labeled-image"
    s3_prefix_root = os.environ.get("S3_PREFIX", "labeled-image").strip("/")
    print(f"[lambda_handler] Prefix: {prefix}, Label Studio URL: {label_studio_url}, S3 Bucket: {s3_bucket}, S3 Root Prefix: {s3_prefix_root}")

    # Lấy thông tin bucket/prefix ảnh gốc của project
    src_image_bucket, src_image_prefix = get_project_s3_storage(label_studio_url, api_key, project_id)
    print(f"[lambda_handler] Source Image Bucket: {src_image_bucket}, Prefix: {src_image_prefix}")

    export_url = f"{label_studio_url}/api/projects/{project_id}/export?exportType=YOLO"
    headers = {'Authorization': f'Token {api_key}'}
    print(f"[lambda_handler] Export URL: {export_url}")

    resp = _http.get(export_url, headers=headers, timeout=HTTP_TIMEOUT)
    print(f"[lambda_handler] Export annotation response status: {resp.status_code}")
    if resp.status_code != 200:
        print(f"[lambda_handler] ERROR: {resp.text}")
        raise Exception(f"Label Studio export failed: {resp.text}")

    s3_client = boto3.client('s3')

    with tempfile.TemporaryDirectory() as tmpdir:
        zip_path = os.path.join(tmpdir, 'annotation_yolo.zip')
        with open(zip_path, 'wb') as f:
            f.write(resp.content)
        print(f"[lambda_handler] Annotation zip downloaded to {zip_path}")

        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            _safe_extract_all(zip_ref, Path(tmpdir))
        print(f"[lambda_handler] Zip extracted to {tmpdir}")

        for root, dirs, files in os.walk(tmpdir):
            for filename in files:
                if filename.endswith('.zip'):
                    continue
                local_path = os.path.join(root, filename)
                print(f"[lambda_handler] Processing file: {local_path}")

                if filename == 'classes.txt':
                    s3_key = f"{s3_prefix_root}/{prefix}/classes.txt"
                    s3_client.upload_file(local_path, s3_bucket, s3_key)
                    print(f"[lambda_handler] Uploaded {local_path} to s3://{s3_bucket}/{s3_key}")

                elif filename.endswith('.txt'):
                    if '__' in filename:
                        new_filename = filename.split('__', 1)[1]
                    else:
                        new_filename = filename
                    s3_key = f"{s3_prefix_root}/{prefix}/labels/{new_filename}"
                    s3_client.upload_file(local_path, s3_bucket, s3_key)
                    print(f"[lambda_handler] Uploaded {local_path} to s3://{s3_bucket}/{s3_key}")

                    image_base = os.path.splitext(new_filename)[0]
                    found_image = False
                    for ext in ['.jpg', '.jpeg', '.png']:
                        src_key = f"{src_image_prefix}{image_base}{ext}"
                        print(f"[lambda_handler] Trying to copy image: s3://{src_image_bucket}/{src_key}")
                        try:
                            s3_client.head_object(Bucket=src_image_bucket, Key=src_key)
                            dest_image_key = f"{s3_prefix_root}/{prefix}/images/{image_base}{ext}"
                            s3_client.copy_object(
                                CopySource={'Bucket': src_image_bucket, 'Key': src_key},
                                Bucket=s3_bucket,
                                Key=dest_image_key
                            )
                            print(f"[lambda_handler] Copied image: {src_image_bucket}/{src_key} -> {s3_bucket}/{dest_image_key}")
                            found_image = True
                            break
                        except ClientError as e:
                            code = e.response.get("Error", {}).get("Code")
                            status = e.response.get("ResponseMetadata", {}).get("HTTPStatusCode")
                            if code in {"NoSuchKey"} or status == 404:
                                print(f"[lambda_handler] Not found: {src_key}")
                                continue
                            else:
                                print(f"[lambda_handler] Error copying image {src_key}: {e}")
                                continue
                        except Exception as e:
                            print(f"[lambda_handler] Error copying image {src_key}: {e}")
                            continue
                    if not found_image:
                        print(f"[lambda_handler] Image not found for label: {image_base}")

                elif filename.lower().endswith(('.jpg', '.jpeg', '.png')):
                    s3_key = f"{s3_prefix_root}/{prefix}/images/{filename}"
                    s3_client.upload_file(local_path, s3_bucket, s3_key)
                    print(f"[lambda_handler] Uploaded {local_path} to s3://{s3_bucket}/{s3_key}")

                else:
                    s3_key = f"{s3_prefix_root}/{prefix}/{filename}"
                    s3_client.upload_file(local_path, s3_bucket, s3_key)
                    print(f"[lambda_handler] Uploaded {local_path} to s3://{s3_bucket}/{s3_key}")

    print(f"[lambda_handler] DONE for project_id={project_id}")
    return {
        "status": "DONE",
        "bucket": s3_bucket,
        "prefix": f"{s3_prefix_root}/{prefix}/",
        "project_id": project_id
    }
