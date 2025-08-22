#!/usr/bin/env python3
import os

import aws_cdk as cdk

from planogram_project_cdk.stacks import (
    ExportAnnotationsLambdaCdkStack,
    CreateTrainingJobLambdaCdkStack,
    CreateEndpointLambdaCdkStack,
    S3BucketStack,
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

s3_bucket_stack = S3BucketStack(
    app,
    "S3BucketCdkStack",
    env=env,
)

app.synth()
