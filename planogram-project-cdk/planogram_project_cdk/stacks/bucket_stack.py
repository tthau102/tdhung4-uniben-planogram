from aws_cdk import (
    Stack,
    aws_s3 as s3,
    aws_s3_deployment as s3_deployment,
    aws_s3_notifications as s3n,
    CfnOutput,
    custom_resources as cr,
    aws_iam as iam,
)
from constructs import Construct


class S3BucketCdkStack(Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        invoke_yolo_lambda_cdk_stack=None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.source_bucket = s3.Bucket(
            self,
            "planogram_source_bucket",
            versioned=False,
            # removal_policy=cdk.RemovalPolicy.DESTROY,
            # auto_delete_objects=True,
        )

        s3_deployment.BucketDeployment(
            self,
            "CreateImageFolder",
            destination_bucket=self.source_bucket,
            sources=[s3_deployment.Source.data("images/", "")],
        )

        # if (
        #     invoke_yolo_lambda_cdk_stack
        #     and invoke_yolo_lambda_cdk_stack.invoke_yolo_function
        # ):
        #     # Grant S3 read permissions to Lambda
        #     self.source_bucket.grant_read(
        #         invoke_yolo_lambda_cdk_stack.invoke_yolo_function
        #     )

        #     # Add event notification for object creation
        #     # self.source_bucket.add_event_notification(
        #     #     s3.EventType.OBJECT_CREATED,
        #     #     s3n.LambdaDestination(
        #     #         invoke_yolo_lambda_cdk_stack.invoke_yolo_function
        #     #     ),
        #     #     s3.NotificationKeyFilter(prefix="test-images/", suffix=".jpg"),
        #     # )

        #     # invoke_yolo_lambda_stack.invoke_yolo.add_environment(
        #     #     "SOURCE_BUCKET_NAME",
        #     #     self.planogram_source_bucket.bucket_name
        #     # )

        #     notification_resource = cr.AwsCustomResource(
        #         self,
        #         "S3NotificationResource",
        #         on_create=cr.AwsSdkCall(
        #             service="S3",
        #             action="putBucketNotificationConfiguration",
        #             parameters={
        #                 "Bucket": self.source_bucket.bucket_name,
        #                 "NotificationConfiguration": {
        #                     "LambdaFunctionConfigurations": [
        #                         {
        #                             "Id": "YOLOProcessingTrigger",
        #                             "LambdaFunctionArn": invoke_yolo_lambda_cdk_stack.invoke_yolo_function.function_arn,
        #                             "Events": ["s3:ObjectCreated:*"],
        #                             "Filter": {
        #                                 "Key": {
        #                                     "FilterRules": [
        #                                         {"Name": "prefix", "Value": "images/"},
        #                                         {"Name": "suffix", "Value": ".jpg"},
        #                                     ]
        #                                 }
        #                             },
        #                         }
        #                     ]
        #                 },
        #             },
        #             physical_resource_id=cr.PhysicalResourceId.of(
        #                 f"S3Notification-{self.source_bucket.bucket_name}"
        #             ),
        #         ),
        #         on_delete=cr.AwsSdkCall(
        #             service="S3",
        #             action="putBucketNotificationConfiguration",
        #             parameters={
        #                 "Bucket": self.source_bucket.bucket_name,
        #                 "NotificationConfiguration": {},
        #             },
        #         ),
        #         policy=cr.AwsCustomResourcePolicy.from_statements(
        #             [
        #                 iam.PolicyStatement(
        #                     actions=["s3:PutBucketNotificationConfiguration"],
        #                     resources=[self.source_bucket.bucket_arn],
        #                 )
        #             ]
        #         ),
        #         # log_retention=logs.RetentionDays.ONE_DAY,
        #     )

        #     # Ensure the notification is created after the bucket
        #     notification_resource.node.add_dependency(self.source_bucket)

        self.training_bucket = s3.Bucket(
            self,
            "planogram_training_bucket",
            versioned=False,
            # removal_policy=cdk.RemovalPolicy.DESTROY,
            # auto_delete_objects=True,
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
            # removal_policy=cdk.RemovalPolicy.DESTROY,
            # auto_delete_objects=True,
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
            "SourceBucketName",
            value=self.source_bucket.bucket_name,
            description="",
        )

        CfnOutput(
            self,
            "SourceBucketArn",
            value=self.source_bucket.bucket_arn,
            description="",
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
