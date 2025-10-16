from aws_cdk import (
    Stack,
    aws_s3 as s3,
    CfnOutput,
    custom_resources as cr,
    aws_iam as iam,
    RemovalPolicy,
    aws_s3_deployment as s3_deployment,
)
from constructs import Construct


class S3BucketCdkStack(Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: dict,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.stack_config = config["s3_bucket_cdk_stack"]

        self.training_bucket = s3.Bucket(
            self,
            "planogram_training",
            versioned=False,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        s3_deployment.BucketDeployment(
            self,
            "CreateTrainingModelFolder",
            destination_bucket=self.training_bucket,
            sources=[s3_deployment.Source.data("tranining-model/.keep", "")],
        )

        s3_deployment.BucketDeployment(
            self,
            "CreateLabeledImageFolder",
            destination_bucket=self.training_bucket,
            sources=[s3_deployment.Source.data("labeled-image/.keep", "")],
        )

        CfnOutput(
            self,
            "TrainingBucketName",
            value=self.training_bucket.bucket_name,
            description="",
        )

        CfnOutput(
            self,
            "TrainingBucketArn",
            value=self.training_bucket.bucket_arn,
            description="",
        )
