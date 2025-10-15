# import psycopg2
# from psycopg2.extras import Json
import os
import boto3
import json
import base64
from invoke_gen_ai import invoke_claude, invoke_nova
from invoke_ml_model import invoke_YOLO
from detect_product import extract_shelves_and_bottles, organize_bottles_by_shelf
from create_annotated_image import draw_boxes_and_upload_to_S3
from get_creds import get_secret
from fix_json import fix_json_structure
from typing import Dict, Any, Optional, Union
from dynamodb_writer import DynamoDBWriter


def lambda_handler(event, context):

    bucketName, imageKey = (
        event["Records"][0]["s3"]["bucket"]["name"],
        event["Records"][0]["s3"]["object"]["key"],
    )

    annotated_image_bucket = os.getenv("ANNOTATED_BUCKET")
    s3 = boto3.client("s3")
    image_data = s3.get_object(Bucket=bucketName, Key=imageKey)
    image_bytes = image_data["Body"].read()
    print("Get image from S3 successfully")

    detections, originalImage = invoke_YOLO(image_bytes)
    annotatedImageKey = draw_boxes_and_upload_to_S3(
        s3, bucketName, imageKey, detections, originalImage
    )
    shelves, bottles = extract_shelves_and_bottles(detections)
    shelf_result = organize_bottles_by_shelf(shelves, bottles)
    # print(shelf_result)

    json_result = invoke_claude(shelf_result)[1]

    json_result = fix_json_structure(json_result)

    llm_result = json.loads(json_result)

    compliance_assessment = llm_result["refrigerator_analysis"]["target_image_met"]
    need_review = llm_result["refrigerator_analysis"]["need_review"]
    review_comment = llm_result["refrigerator_analysis"]["review_comment"]

    dynamo_writer = DynamoDBWriter(os.getenv("DB_NAME"))
    dynamo_writer.write_single_item(
        item_data={
            "image_name": event["Records"][0]["s3"]["object"]["key"],
            "s3_url": f"https://{annotated_image_bucket}.s3.ap-southeast-1.amazonaws.com/{annotatedImageKey}",
            "product_count": json.dumps(shelf_result),
            "compliance_assessment": compliance_assessment,
            "need_review": need_review,
            "review_comment": review_comment,
        }
    )
    print("Write result to DB successfully!")

    print("All done!")
