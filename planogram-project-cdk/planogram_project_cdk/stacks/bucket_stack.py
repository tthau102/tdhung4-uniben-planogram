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
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.training_bucket = s3.Bucket(
            self,
            "planogram_training_bucket",
            versioned=False,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        s3_deployment.BucketDeployment(
            self,
            "CreateTrainingModelFolder",
            destination_bucket=self.training_bucket,
            sources=[s3_deployment.Source.data("tranining-model/", "")],
        )

        s3_deployment.BucketDeployment(
            self,
            "CreateLabeledImageFolder",
            destination_bucket=self.training_bucket,
            sources=[s3_deployment.Source.data("labeled-image/", "")],
        )

        self.test_bucket = s3.Bucket(
            self,
            "planogram_test_bucket",
            versioned=False,
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
        )

        s3_deployment.BucketDeployment(
            self,
            "CreateAnnotatedImageFolder",
            destination_bucket=self.test_bucket,
            sources=[s3_deployment.Source.data("annotated-images/", "")],
        )

        s3_deployment.BucketDeployment(
            self,
            "CreateTestImageFolder",
            destination_bucket=self.test_bucket,
            sources=[s3_deployment.Source.data("test-images/", "")],
        )

        # Tags.of(self.source_bucket).add("project", "planogram")
        # Tags.of(self.training_bucket).add("project", "planogram")
        # Tags.of(self.test_bucket).add("project", "planogram")

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

        CfnOutput(
            self,
            "TestBucketName",
            value=self.test_bucket.bucket_name,
            description="",
        )

        CfnOutput(
            self,
            "TestBucketArn",
            value=self.test_bucket.bucket_arn,
            description="",
        )
