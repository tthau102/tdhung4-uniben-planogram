from aws_cdk import (
    Stack,
    custom_resources as cr,
    aws_iam as iam,
    CfnOutput,
)
from constructs import Construct


class BedrockInferenceProfileStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.profile_name = "planogram-inference-profile"
        self.inference_profile = cr.AwsCustomResource(
            self,
            "BedrockInferenceProfile",
            on_create=cr.AwsSdkCall(
                service="Bedrock",
                action="createInferenceProfile",
                parameters={
                    "inferenceProfileName": self.profile_name,
                    "description": "Claude Inference Profile",
                    "modelSource": {
                        "copyFrom": "arn:aws:bedrock:ap-southeast-1::foundation-model/anthropic.claude-3-5-sonnet-20240620-v1:0"
                    },
                },
                physical_resource_id=cr.PhysicalResourceId.of(self.profile_name),
            ),
            on_update=cr.AwsSdkCall(
                service="Bedrock",
                action="getInferenceProfile",
                parameters={"inferenceProfileIdentifier": self.profile_name},
                physical_resource_id=cr.PhysicalResourceId.of(self.profile_name),
            ),
            on_delete=cr.AwsSdkCall(
                service="Bedrock",
                action="deleteInferenceProfile",
                parameters={
                    # Use the profile name directly instead of reference
                    "inferenceProfileIdentifier": self.profile_name
                },
            ),
            policy=cr.AwsCustomResourcePolicy.from_statements(
                [
                    iam.PolicyStatement(
                        actions=[
                            "bedrock:CreateInferenceProfile",
                            "bedrock:DeleteInferenceProfile",
                            "bedrock:GetInferenceProfile",
                        ],
                        resources=["*"],
                    )
                ]
            ),
        )

        self.profileARN = self.inference_profile.get_response_field(
            "inferenceProfileArn"
        )

        CfnOutput(
            self,
            "ProfileARN",
            value=self.profileARN,
            description="Inference Profile",
        )
