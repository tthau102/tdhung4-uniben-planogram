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


class CreateEndpointLambdaCdkStack(Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: dict,
        lambda_layers_stack=None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.stack_config = config["create_endpoint_lambda_cdk_stack"]

        self.create_endpoint_lambda_role = iam.Role(
            self,
            "create_endpoint_lambda-role",
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
            ],
        )

        # Endpoint role
        self.endpoint_role = iam.Role(
            self,
            "yolo-endpoint-role",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole",
                ),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "AmazonSageMakerFullAccess"
                ),
            ],
        )

        self.sagemaker_layer = lambda_.LayerVersion.from_layer_version_arn(
            self,
            "SageMakerLayer",
            lambda_layers_stack.sagemaker_layer.layer_version_arn,
        )

        self.create_endpoint_function = lambda_.Function(
            self,
            "create_endpoint",
            runtime=lambda_.Runtime.PYTHON_3_11,
            code=lambda_.Code.from_asset("lambda/2_create_endpoint"),
            handler="lambda_function.lambda_handler",
            timeout=Duration.seconds(900),
            memory_size=512,
            ephemeral_storage_size=Size.mebibytes(1024),
            role=self.create_endpoint_lambda_role,
            layers=[self.sagemaker_layer],
            environment={
                "S3_MODEL_BUCKET": "s3://uniben-planogram-training/tranining-model",
                "ENDPOINT_ROLE": f"{self.endpoint_role.role_arn}",
            },
            description="Create Endpoint on Amazon SageMaker",
        )

        CfnOutput(
            self,
            "LambdaFunctionArn",
            value=self.create_endpoint_function.function_arn,
            description="ARN create_endpoint function",
        )

        CfnOutput(
            self,
            "LambdaFunctionName",
            value=self.create_endpoint_function.function_name,
            description="create_endpoint function",
        )
