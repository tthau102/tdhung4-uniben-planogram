from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    Tags,
    Size,
    RemovalPolicy,
    aws_lambda as lambda_,
    aws_iam as iam,
)
from constructs import Construct


class CreateEndpointLambdaCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.create_endpoint_lambda_role = iam.Role(
            self,
            "create_endpoint-lambda-role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole",
                )
            ],
        )

        self.create_endpoint_lambda_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess")
        )
        self.create_endpoint_lambda_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess")
        )
        self.create_endpoint_lambda_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AWSLambda_FullAccess")
        )

        # Endpoint role
        self.endpoint_role = iam.Role(
            self,
            "endpoint-role",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
        )

        self.endpoint_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess")
        )
        self.endpoint_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonBedrockFullAccess")
        )
        self.endpoint_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AWSLambda_FullAccess")
        )

        # dependencies_layer = lambda_.LayerVersion(
        #     self, "DependenciesLayer",
        #     code=lambda_.Code.from_asset("layers/dependencies"),
        #     compatible_runtimes=[lambda_.Runtime.PYTHON_3_9],
        #     description="Common dependencies"
        # )

        self.sagemaker_layer = lambda_.LayerVersion.from_layer_version_arn(
            self,
            "SageMakerLayer",
            "arn:aws:lambda:ap-southeast-1:151182331915:layer:sagemaker:1",
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
                "MODEL_ROLE": f"",
            },
            description="Create Endpoint on Amazon SageMaker",
        )

        Tags.of(self.create_endpoint_function).add("project", "planogram")

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
