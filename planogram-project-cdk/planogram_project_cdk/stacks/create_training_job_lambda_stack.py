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


class CreateTrainingJobLambdaCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.create_training_job_policy = iam.Policy(
            self,
            "create_training_job-policy",
            policy_name="create_training_job-policy",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=[
                        "sagemaker:CreateTrainingJob",
                        "sagemaker:DescribeTrainingJob",
                        "sagemaker:StopTrainingJob",
                        "sagemaker:ListTrainingJobs",
                        "sagemaker:AddTags",
                        "iam:PassRole",
                        "s3:GetObject",
                        "s3:PutObject",
                        "s3:ListBucket",
                        "ecr:GetAuthorizationToken",
                        "ecr:BatchCheckLayerAvailability",
                        "ecr:GetDownloadUrlForLayer",
                        "ecr:BatchGetImage",
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents",
                    ],
                    resources=["*"],
                ),
            ],
        )

        self.create_training_job_lambda_role = iam.Role(
            self,
            "create_training_job-lambda-role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                )
            ],
        )

        self.create_training_job_policy.attach_to_role(
            self.create_training_job_lambda_role
        )

        self.create_training_job_function = lambda_.Function(
            self,
            "create_training_job",
            runtime=lambda_.Runtime.PYTHON_3_11,
            code=lambda_.Code.from_asset("lambda/1_create_training_job"),
            handler="lambda_function.lambda_handler",
            timeout=Duration.seconds(30),
            memory_size=128,
            ephemeral_storage_size=Size.mebibytes(512),
            role=self.create_training_job_lambda_role,
            environment={
                "SAGEMAKER_ROLE_ARN": "arn:aws:iam::151182331915:role/training_job_role",
                "ECR_IMAGE_URI": "151182331915.dkr.ecr.ap-southeast-1.amazonaws.com/yolo11-training:latest",
                # "REGION": Stack.of(self).region,
            },
            description="Create YOLO11x Training job on Amazon SageMaker",
        )

        CfnOutput(
            self,
            "LambdaFunctionArn",
            value=self.create_training_job_function.function_arn,
            description="ARN create_training_job function",
        )

        CfnOutput(
            self,
            "LambdaFunctionName",
            value=self.create_training_job_function.function_name,
            description="create_training_job function",
        )
