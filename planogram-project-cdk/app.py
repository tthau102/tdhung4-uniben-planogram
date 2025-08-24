#!/usr/bin/env python3
import os

import aws_cdk as cdk

from planogram_project_cdk.stacks import (
    ExportAnnotationsLambdaCdkStack,
    CreateTrainingJobLambdaCdkStack,
    CreateEndpointLambdaCdkStack,
    InvokeYOLOLambdaCdkStack,
    S3BucketCdkStack,
    BedrockInferenceProfileStack,
)
from aws_cdk import (
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    aws_lambda_event_sources as event_sources,
)

app = cdk.App()

env = cdk.Environment(
    account=os.getenv("CDK_DEFAULT_ACCOUNT"), region=os.getenv("CDK_DEFAULT_REGION")
)

export_annotations_lambda_stack = ExportAnnotationsLambdaCdkStack(
    app,
    "ExportAnnotationsLambdaCdkStack",
    env=env,
)

create_training_job_lambda_stack = CreateTrainingJobLambdaCdkStack(
    app,
    "CreateTrainingJobLambdaCdkStack",
    env=env,
)

create_endpoint_lambda_stack = CreateEndpointLambdaCdkStack(
    app,
    "CreateEndpointLambdaCdkStack",
    env=env,
)

source_bucket_and_invoke_yolo_lambda_stack = InvokeYOLOLambdaCdkStack(
    app,
    "InvokeYOLOLambdaCdkStack",
    env=env,
)

s3_bucket_stack = S3BucketCdkStack(
    app,
    "S3BucketCdkStack",
    env=env,
)

bedrock_inference_profile_stack = BedrockInferenceProfileStack(
    app,
    "BedrockInferenceProfileCdkStack",
    env=env,
)


for stack in [
    export_annotations_lambda_stack,
    create_training_job_lambda_stack,
    create_endpoint_lambda_stack,
    source_bucket_and_invoke_yolo_lambda_stack,
    s3_bucket_stack,
    bedrock_inference_profile_stack,
]:
    cdk.Tags.of(stack).add("project", "planogram")

app.synth()
