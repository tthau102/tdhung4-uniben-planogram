#!/usr/bin/env python3
import os

import aws_cdk as cdk

from planogram_project_cdk.stacks import (
    ExportAnnotationsLambdaCdkStack,
    CreateTrainingJobLambdaCdkStack,
    CreateEndpointLambdaCdkStack,
    InvokeYOLOLambdaCdkStack,
    S3BucketCdkStack,
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

invoke_yolo_lambda_stack = InvokeYOLOLambdaCdkStack(
    app,
    "InvokeYOLOLambdaCdkStack",
    env=env,
)

s3_bucket_stack = S3BucketCdkStack(
    app,
    "S3BucketCdkStack",
    env=env,
    # invoke_yolo_lambda_cdk_stack=invoke_yolo_lambda_stack,
)


# s3_bucket_stack.add_dependency(invoke_yolo_lambda_stack)

# if invoke_yolo_lambda_stack and invoke_yolo_lambda_stack.invoke_yolo_function:
#     # Grant S3 read permissions to Lambda
#     s3_bucket_stack.source_bucket.grant_read(
#         invoke_yolo_lambda_stack.invoke_yolo_function,
#     )

#     # Add event notification for object creation
#     s3_bucket_stack.source_bucket.add_event_notification(
#         s3.EventType.OBJECT_CREATED,
#         s3n.LambdaDestination(invoke_yolo_lambda_stack.invoke_yolo_function),
#         s3.NotificationKeyFilter(prefix="test-images/", suffix=".jpg"),
#     )

# Add S3 event source to Lambda after both stacks are created
# invoke_yolo_lambda_stack.invoke_yolo_function.add_event_source(
#     event_sources.S3EventSource(
#         s3_bucket_stack.source_bucket,
#         events=[s3.EventType.OBJECT_CREATED],
#         filters=[s3.NotificationKeyFilter(prefix="images/", suffix=".jpg")],
#     )
# )

# # Grant permissions
# s3_bucket_stack.source_bucket.grant_read_write(
#     invoke_yolo_lambda_stack.invoke_yolo_function
# )


for stack in [
    export_annotations_lambda_stack,
    create_training_job_lambda_stack,
    create_endpoint_lambda_stack,
    invoke_yolo_lambda_stack,
    s3_bucket_stack,
]:
    cdk.Tags.of(stack).add("project", "planogram")

app.synth()
