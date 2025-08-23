import psycopg2
from psycopg2.extras import Json
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

def clearTable(conn, cursor):
    table = "planogram_test"
    delete_query = f"DELETE FROM {table}"
    cursor.execute(delete_query)
    conn.commit()

def connectDB():
    creds = json.loads(get_secret())

    DB_CONFIG = {
        "host": creds["host"],
        "port": creds["port"],
        "user": creds["username"],
        "password": creds["password"],
        "database": os.getenv("DB_NAME"),
    }

    try:
        conn = psycopg2.connect(**DB_CONFIG)
        if conn:
            print("Connect to database successfully")
            return conn
    except Exception as e:
        print("Fail to connect to database", e)

def writeResultToDB(conn, cursor, analyzeResult):
    table = "results" 
    insert_query = f"""
        INSERT INTO {table} (image_name, s3_url, product_count, compliance_assessment, need_review, review_comment)
        VALUES (%s, %s, %s, %s, %s, %s);
    """
    cursor.execute(insert_query, (analyzeResult["image_name"], 
                                    analyzeResult["s3_url"],
                                    analyzeResult["product_count"],
                                    analyzeResult["compliance_assessment"],
                                    analyzeResult["need_review"],
                                    analyzeResult["review_comment"],))
    print("Write result to DB successfully")
    conn.commit()


def lambda_handler(event, context):
    # print(event)
    conn = connectDB()
    cursor = conn.cursor()

    bucketName, imageKey = event["Records"][0]["s3"]["bucket"]["name"], event["Records"][0]["s3"]["object"]["key"]
    annotated_image_bucket="uniben-planogram-test"
    s3 = boto3.client('s3')
    image_data = s3.get_object(Bucket=bucketName, Key=imageKey)
    image_bytes = image_data['Body'].read()
    print("Get image from S3 successfully")

    detections, originalImage = invoke_YOLO(image_bytes)
    annotatedImageKey = draw_boxes_and_upload_to_S3(s3, bucketName, imageKey, detections, originalImage)
    shelves, bottles = extract_shelves_and_bottles(detections)
    shelf_result = organize_bottles_by_shelf(shelves, bottles)
    # print(shelf_result)

    json_result = invoke_claude(shelf_result)[1]

    json_result = fix_json_structure(json_result)

    llm_result = json.loads(json_result)

    compliance_assessment = llm_result["refrigerator_analysis"]["target_image_met"]
    need_review = llm_result["refrigerator_analysis"]["need_review"]
    review_comment = llm_result["refrigerator_analysis"]["review_comment"]

    writeResultToDB(conn, cursor, {
        "image_name": event["Records"][0]["s3"]["object"]["key"], 
        "s3_url": f"https://{annotated_image_bucket}.s3.ap-southeast-1.amazonaws.com/{annotatedImageKey}", 
        "product_count": Json(shelf_result),
        "compliance_assessment": compliance_assessment,
        "need_review": need_review,
        "review_comment": review_comment,
        }
    )

    cursor.close()
    conn.close()

    print("All done!")
