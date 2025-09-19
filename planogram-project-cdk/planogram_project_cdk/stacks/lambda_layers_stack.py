from aws_cdk import (
    Stack,
    RemovalPolicy,
    CfnOutput,
    aws_lambda as lambda_,
    aws_s3 as s3,
)
from constructs import Construct


class LambdaLayersStack(Stack):
    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        config: dict,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.stack_config = config.get("lambda_layers_cdk_stack", {})

        # OpenCV Layer
        self.opencv_layer = lambda_.LayerVersion(
            self,
            "OpenCVLayer",
            code=lambda_.S3Code(
                bucket=s3.Bucket.from_bucket_name(
                    self,
                    "OpenCVLayerBucket",
                    bucket_name=self.stack_config.get(
                        "opencv_layer_bucket_name", "default-layer-bucket"
                    ),
                ),
                key=self.stack_config.get("opencv_layer_s3_key", "layers/opencv.zip"),
            ),
            compatible_runtimes=[
                lambda_.Runtime.PYTHON_3_11,
            ],
            layer_version_name=self.stack_config.get(
                "opencv_layer_name", "PlanogramOpenCVLayer"
            ),
            description="OpenCV Lambda layer for Planogram project",
            removal_policy=RemovalPolicy.DESTROY,
        )

        # SageMaker Layer
        self.sagemaker_layer = lambda_.LayerVersion(
            self,
            "SageMakerLayer",
            code=lambda_.S3Code(
                bucket=s3.Bucket.from_bucket_name(
                    self,
                    "SageMakerLayerBucket",
                    bucket_name=self.stack_config.get(
                        "sagemaker_layer_bucket_name", "default-layer-bucket"
                    ),
                ),
                key=self.stack_config.get(
                    "sagemaker_layer_s3_key", "layers/sagemaker.zip"
                ),
            ),
            compatible_runtimes=[
                lambda_.Runtime.PYTHON_3_11,
            ],
            layer_version_name=self.stack_config.get(
                "sagemaker_layer_name", "PlanogramSageMakerLayer"
            ),
            description="SageMaker Lambda layer for Planogram project",
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Output the layer ARNs for reference
        CfnOutput(
            self,
            "OpenCVLayerArn",
            value=self.opencv_layer.layer_version_arn,
            description="ARN of the OpenCV Lambda layer",
            export_name="planogram-opencv-layer-arn",
        )

        CfnOutput(
            self,
            "SageMakerLayerArn",
            value=self.sagemaker_layer.layer_version_arn,
            description="ARN of the SageMaker Lambda layer",
            export_name="planogram-sagemaker-layer-arn",
        )
