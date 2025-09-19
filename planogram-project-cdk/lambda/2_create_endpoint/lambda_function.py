import boto3
import sagemaker
import os
import json
from sagemaker.model import Model
from sagemaker.predictor import Predictor
from datetime import datetime


def lambda_handler(event, context):
    print(event)
    sagemaker_session = sagemaker.Session()

    # model_data = f's3://uniben-data/output_lambda/yolo11x-20250804-093828/output/model.tar.gz'
    # model_data = f's3://uniben-planogram-training/tranining-model/{event.get("train_folder")}/output/model.tar.gz'
    model_data = f'{os.getenv("S3_MODEL_BUCKET")}/{event.get("train_folder")}/output/model.tar.gz'
    model_name = f'yolo11x-model-{datetime.now().strftime("%Y%m%d-%H%M%S")}'
    endpoint_name = f'yolo11x-endpoint-{datetime.now().strftime("%Y%m%d-%H%M%S")}'
    region = boto3.Session().region_name
    pytorch_inference_image = sagemaker.image_uris.retrieve(
        framework="pytorch",
        region=region,
        version="2.0.0",
        py_version="py310",
        image_scope="inference",
        instance_type=event.get("instance_type", "ml.m5.xlarge"),
    )

    model = Model(
        model_data=model_data,
        image_uri=pytorch_inference_image,
        # role="arn:aws:iam::151182331915:role/YOLO11SageMakerStack-yolo11notebookAccessRole4FE3B3-EdP6dF8ALap0",
        role=os.getenv("ENDPOINT_ROLE"),
        name=model_name,
        sagemaker_session=sagemaker_session,
        env={
            "SAGEMAKER_PROGRAM": "inference.py",
            "SAGEMAKER_SUBMIT_DIRECTORY": model_data,
            "SAGEMAKER_REGION": region,
            "TS_MAX_RESPONSE_SIZE": "20000000",
            "YOLO11_MODEL": "model.pt",
        },
    )

    predictor = model.deploy(
        initial_instance_count=1,
        instance_type=event.get("instance_type", "ml.m5.xlarge"),
        endpoint_name=endpoint_name,
        tags=[
            {"Key": "project", "Value": "planogram"},
        ],
    )

    print(f"Model deployed successfully!")
    print(f"Model name: {model_name}")
    print(f"Endpoint name: {endpoint_name}")

    return {
        "statusCode": 200,
        "body": {
            "model_data": model_data,
            "model_name": model_name,
            "endpoint_name": endpoint_name,
        },
    }
