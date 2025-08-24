from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    Tags,
    Size,
    RemovalPolicy,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_s3_deployment as s3_deployment,
    aws_s3_notifications as s3n,
    aws_s3 as s3,
)
from constructs import Construct


class InvokeYOLOLambdaCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.source_bucket = s3.Bucket(
            self,
            "planogram_source_bucket",
            versioned=False,
            removal_policy=RemovalPolicy.DESTROY,
            # auto_delete_objects=True,
            # block_public_access=s3.BlockPublicAccess.BLOCK_ALL
        )

        s3_deployment.BucketDeployment(
            self,
            "CreateImageFolder",
            destination_bucket=self.source_bucket,
            sources=[s3_deployment.Source.data("images/", "")],
        )

        self.invoke_yolo_lambda_role = iam.Role(
            self,
            "invoke_yolo_lambda-role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole",
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonSageMakerFullAccess"
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name("AWSLambda_FullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonBedrockFullAccess"
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2FullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonVPCFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "SecretsManagerReadWrite"
                ),
            ],
        )

        # self.invoke_yolo_lambda_role.add_managed_policy(
        #     iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess")
        # )
        # self.invoke_yolo_lambda_role.add_managed_policy(
        #     iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess")
        # )
        # self.invoke_yolo_lambda_role.add_managed_policy(
        #     iam.ManagedPolicy.from_aws_managed_policy_name("AWSLambda_FullAccess")
        # )
        # self.invoke_yolo_lambda_role.add_managed_policy(
        #     iam.ManagedPolicy.from_aws_managed_policy_name("AmazonBedrockFullAccess")
        # )
        # self.invoke_yolo_lambda_role.add_managed_policy(
        #     iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2FullAccess")
        # )
        # self.invoke_yolo_lambda_role.add_managed_policy(
        #     iam.ManagedPolicy.from_aws_managed_policy_name("AmazonVPCFullAccess")
        # )
        # self.invoke_yolo_lambda_role.add_managed_policy(
        #     iam.ManagedPolicy.from_aws_managed_policy_name("SecretsManagerReadWrite")
        # )

        self.opencv_layer = lambda_.LayerVersion.from_layer_version_arn(
            self,
            "OpenCVLayer",
            "arn:aws:lambda:ap-southeast-1:151182331915:layer:opencv:5",
        )

        self.invoke_yolo_function = lambda_.Function(
            self,
            "invoke_yolo",
            runtime=lambda_.Runtime.PYTHON_3_11,
            code=lambda_.Code.from_asset("lambda/3_invoke_yolo"),
            handler="lambda_function.lambda_handler",
            timeout=Duration.seconds(300),
            memory_size=512,
            ephemeral_storage_size=Size.mebibytes(2048),
            role=self.invoke_yolo_lambda_role,
            layers=[self.opencv_layer],
            # environment={
            #     "S3_MODEL_BUCKET": "a",
            # },
            description="Invoke YOLO",
        )

        # Grant Lambda permissions to read/write S3 bucket
        self.source_bucket.grant_read_write(self.invoke_yolo_function)

        # Add S3 trigger to Lambda
        self.source_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(self.invoke_yolo_function),
            s3.NotificationKeyFilter(prefix="images/", suffix=".jpg"),
        )

        CfnOutput(
            self,
            "BucketName",
            value=self.source_bucket.bucket_name,
            description="S3 Bucket Name",
        )

        CfnOutput(
            self,
            "LambdaFunctionArn",
            value=self.invoke_yolo_function.function_arn,
            description="ARN invoke_yolo function",
        )

        CfnOutput(
            self,
            "LambdaFunctionName",
            value=self.invoke_yolo_function.function_name,
            description="invoke_yolo function",
        )
