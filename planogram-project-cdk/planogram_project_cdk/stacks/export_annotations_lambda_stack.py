from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    Size,
    RemovalPolicy,
    aws_lambda as lambda_,
    aws_iam as iam,
)
from constructs import Construct
import os


class ExportAnnotationsLambdaCdkStack(Stack):

    def __init__(
        self, scope: Construct, construct_id: str, config: dict, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.stack_config = config["export_annotations_lambda_cdk_stack"]

        self.export_annotations_lambda_role = iam.Role(
            self,
            "export_annotations_lambda-role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole",
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"),
            ],
        )

        self.export_annotations_function = lambda_.Function(
            self,
            "export_annotations",
            runtime=lambda_.Runtime.PYTHON_3_11,
            code=lambda_.Code.from_asset("lambda/0_export_annotations"),
            handler="lambda_function.lambda_handler",
            timeout=Duration.seconds(900),
            memory_size=512,
            ephemeral_storage_size=Size.mebibytes(512),
            role=self.export_annotations_lambda_role,
            environment={
                "S3_MODEL_BUCKET": "s3://uniben-planogram-training/tranining-model",
            },
            description="Export Annotations from Label Studio",
        )

        CfnOutput(
            self,
            "LambdaFunctionArn",
            value=self.export_annotations_function.function_arn,
            description="ARN export_annotations function",
        )

        CfnOutput(
            self,
            "LambdaFunctionName",
            value=self.export_annotations_function.function_name,
            description="export_annotations function",
        )
