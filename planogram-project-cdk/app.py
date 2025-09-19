#!/usr/bin/env python3
import os
import json

import aws_cdk as cdk

from planogram_project_cdk.stacks import (
    ExportAnnotationsLambdaCdkStack,
    CreateTrainingJobLambdaCdkStack,
    CreateEndpointLambdaCdkStack,
    InvokeYOLOLambdaCdkStack,
    S3BucketCdkStack,
    BedrockInferenceProfileStack,
    VpcAndRdsWithSecretsStack,
    DynamoDbStack,
    LambdaLayersStack,
)
from aws_cdk import (
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    aws_lambda_event_sources as event_sources,
)

app = cdk.App()

# Load configuration
with open("config.json", "r") as config_file:
    config = json.load(config_file)

env = cdk.Environment(
    account=os.getenv("CDK_DEFAULT_ACCOUNT"), region=os.getenv("CDK_DEFAULT_REGION")
)

vpc_and_rds_with_secrets_stack = VpcAndRdsWithSecretsStack(
    app,
    "VpcAndRdsWithSecretsCdkStack",
    config=config,
    env=env,
)

lambda_layers_stack = LambdaLayersStack(
    app,
    "LambdaLayersCDKStack",
    config=config,
    env=env,
)

export_annotations_lambda_stack = ExportAnnotationsLambdaCdkStack(
    app,
    "ExportAnnotationsLambdaCdkStack",
    config=config,
    env=env,
)

create_training_job_lambda_stack = CreateTrainingJobLambdaCdkStack(
    app,
    "CreateTrainingJobLambdaCdkStack",
    config=config,
    env=env,
)

create_endpoint_lambda_stack = CreateEndpointLambdaCdkStack(
    app,
    "CreateEndpointLambdaCdkStack",
    config=config,
    lambda_layers_stack=lambda_layers_stack,
    env=env,
)


source_bucket_and_invoke_yolo_lambda_stack = InvokeYOLOLambdaCdkStack(
    app,
    "InvokeYOLOLambdaCdkStack",
    config=config,
    env=env,
    lambda_layers_stack=lambda_layers_stack,
    vpc_and_rds_with_secrets_stack=vpc_and_rds_with_secrets_stack,
)

table_dynamodb_stack = DynamoDbStack(
    app,
    "DynamoDBCdkStack",
    config=config,
    env=env,
    invoke_yolo_lambda_stack=source_bucket_and_invoke_yolo_lambda_stack,
)

# source_bucket_and_invoke_yolo_lambda_stack.add_dependency(
#     vpc_and_rds_with_secrets_stack
# )

s3_bucket_stack = S3BucketCdkStack(
    app,
    "S3BucketCdkStack",
    config=config,
    env=env,
)

bedrock_inference_profile_stack = BedrockInferenceProfileStack(
    app,
    "BedrockInferenceProfileCdkStack",
    config=config,
    env=env,
)


for stack in [
    vpc_and_rds_with_secrets_stack,
    lambda_layers_stack,
    export_annotations_lambda_stack,
    create_training_job_lambda_stack,
    create_endpoint_lambda_stack,
    source_bucket_and_invoke_yolo_lambda_stack,
    s3_bucket_stack,
    bedrock_inference_profile_stack,
    table_dynamodb_stack,
]:
    cdk.Tags.of(stack).add("project", "planogram")

app.synth()
