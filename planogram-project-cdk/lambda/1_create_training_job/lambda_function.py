import json
import boto3
import os
from datetime import datetime
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

sagemaker = boto3.client("sagemaker")


def lambda_handler(event, context):
    """
    Lambda function to create SageMaker training job for YOLO11x

    Expected event structure:
    {
        "training_data_s3": "s3://your-bucket/path/to/train",
        "validation_data_s3": "s3://your-bucket/path/to/val",
        "output_s3": "s3://your-bucket/path/to/output",
        "instance_type": "ml.g4dn.xlarge",
        "hyperparameters": {
            "epochs": 100,
            "batch-size": 16,
            "learning-rate": 0.01,
            "imgsz": 640
        }
    }
    """

    try:
        training_data = event.get("training_data_s3")
        validation_data = event.get("validation_data_s3")
        output_path = event.get("output_s3")
        instance_type = event.get("instance_type")
        hyperparameters = event.get("hyperparameters", {})

        if not all([training_data, validation_data, output_path]):
            raise ValueError("Missing required S3 paths")

        role_arn = os.getenv("SAGEMAKER_ROLE_ARN")
        ecr_image = os.getenv("ECR_IMAGE_URI")
        # role_arn = f"arn:aws:iam::151182331915:role/training_job_role"
        # ecr_image = (
        #     f"151182331915.dkr.ecr.ap-southeast-1.amazonaws.com/yolo11-training:latest"
        # )

        job_name = f"yolo11x-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

        default_hyperparameters = {
            "epochs": "200",
            "batch-size": "10",
            "imgsz": "640",
            "learning-rate": "0.01",
            "device": "0",
        }

        # Merge with provided hyperparameters
        for key, value in hyperparameters.items():
            default_hyperparameters[key] = str(value)

        training_job_config = {
            "TrainingJobName": job_name,
            "RoleArn": role_arn,
            "AlgorithmSpecification": {
                "TrainingImage": ecr_image,
                "TrainingInputMode": "File",
            },
            "InputDataConfig": [
                {
                    "ChannelName": "train",
                    "DataSource": {
                        "S3DataSource": {
                            "S3DataType": "S3Prefix",
                            "S3Uri": training_data,
                            "S3DataDistributionType": "FullyReplicated",
                        }
                    },
                    "ContentType": "application/x-image",
                },
                {
                    "ChannelName": "validation",
                    "DataSource": {
                        "S3DataSource": {
                            "S3DataType": "S3Prefix",
                            "S3Uri": validation_data,
                            "S3DataDistributionType": "FullyReplicated",
                        }
                    },
                    "ContentType": "application/x-image",
                },
            ],
            "OutputDataConfig": {"S3OutputPath": output_path},
            "ResourceConfig": {
                "InstanceType": instance_type,  # GPU instance for YOLO training
                "InstanceCount": 1,
                "VolumeSizeInGB": 20,
            },
            "StoppingCondition": {"MaxRuntimeInSeconds": 86400},  # 24 hours
            "HyperParameters": default_hyperparameters,
        }

        response = sagemaker.create_training_job(**training_job_config)

        logger.info(f"Training job created: {job_name}")

        return {
            "statusCode": 200,
            "body": json.dumps(
                {
                    "message": "Training job created successfully",
                    "trainingJobName": job_name,
                    "trainingJobArn": response["TrainingJobArn"],
                }
            ),
        }

    except Exception as e:
        logger.error(f"Error creating training job: {str(e)}")
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
