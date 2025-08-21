from constructs import Construct
from aws_cdk import (
    Duration,
    aws_lambda as lambda_,
    aws_iam as iam,
)


class LambdaConstruct(Construct):
    def __init__(
        self,
        scope: Construct,
        id: str,
        function_name: str,
        code_path: str,
        handler: str = "handler.main",
        layers: list = None,
        environment: dict = None,
        **kwargs
    ):
        super().__init__(scope, id)

        self.function = lambda_.Function(
            self,
            function_name,
            runtime=lambda_.Runtime.PYTHON_3_9,
            code=lambda_.Code.from_asset(code_path),
            handler=handler,
            layers=layers or [],
            timeout=Duration.seconds(30),
            memory_size=256,
            environment=environment or {},
            tracing=lambda_.Tracing.ACTIVE,
        )
