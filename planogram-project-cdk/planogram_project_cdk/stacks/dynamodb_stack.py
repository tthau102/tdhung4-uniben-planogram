from aws_cdk import (
    Stack,
    RemovalPolicy,
    CfnOutput,
    CfnResource,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    CustomResource,
    custom_resources as cr,
)
import json
from constructs import Construct


class DynamoDbStack(Stack):

    def __init__(
        self,
        scope: Construct,
        construct_id: str,
        invoke_yolo_lambda_stack=None,
        **kwargs,
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.table = dynamodb.TableV2(
            self,
            "PlanogramResultTable",
            table_name="PlanogramResultTable",
            partition_key=dynamodb.Attribute(
                name="id", type=dynamodb.AttributeType.STRING
            ),
            removal_policy=RemovalPolicy.DESTROY,  # RETAIN
        )

        policy_document = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "AWS": f"{invoke_yolo_lambda_stack.invoke_yolo_lambda_role.role_arn}"
                    },
                    "Action": [
                        "dynamodb:GetItem",
                        "dynamodb:PutItem",
                        "dynamodb:UpdateItem",
                        "dynamodb:DeleteItem",
                        "dynamodb:Query",
                        "dynamodb:Scan",
                    ],
                    "Resource": self.table.table_arn,
                }
            ],
        }

        # Create custom resource to attach policy after table creation
        policy_attachment = cr.AwsCustomResource(
            self,
            "AttachResourcePolicy",
            on_create=cr.AwsSdkCall(
                service="DynamoDB",
                action="putResourcePolicy",
                parameters={
                    "ResourceArn": self.table.table_arn,
                    "Policy": json.dumps(policy_document),
                },
                physical_resource_id=cr.PhysicalResourceId.of(
                    "resource-policy-attachment"
                ),
            ),
            on_update=cr.AwsSdkCall(
                service="DynamoDB",
                action="putResourcePolicy",
                parameters={
                    "ResourceArn": self.table.table_arn,
                    "Policy": json.dumps(policy_document),
                },
            ),
            on_delete=cr.AwsSdkCall(
                service="DynamoDB",
                action="deleteResourcePolicy",
                parameters={"ResourceArn": self.table.table_arn},
            ),
            policy=cr.AwsCustomResourcePolicy.from_statements(
                [
                    iam.PolicyStatement(
                        actions=[
                            "dynamodb:PutResourcePolicy",
                            "dynamodb:DeleteResourcePolicy",
                            "dynamodb:GetResourcePolicy",
                        ],
                        resources=[self.table.table_arn],
                    )
                ]
            ),
        )

        # Ensure policy is attached after table is created
        policy_attachment.node.add_dependency(self.table)

        CfnOutput(
            self,
            "TableName",
            value=self.table.table_name,
            description="DynamoDB Table Name",
        )

        CfnOutput(
            self,
            "TableArn",
            value=self.table.table_arn,
            description="DynamoDB Table ARN",
        )
