from aws_cdk import (
    Stack,
    RemovalPolicy,
    Duration,
    aws_rds as rds,
    aws_ec2 as ec2,
    aws_lambda as lambda_,
    aws_iam as iam,
    CfnOutput,
)
from constructs import Construct
import json


# CIDR Notation Guide:
# /8   = 16,777,216 IPs (Class A)
# /16  = 65,536 IPs (Class B)
# /20  = 4,096 IPs
# /22  = 1,024 IPs
# /24  = 256 IPs (Class C)
# /26  = 64 IPs
# /28  = 16 IPs
# /32  = 1 IP

# Private IP ranges (RFC 1918):
# 10.0.0.0/8     (10.0.0.0 - 10.255.255.255)
# 172.16.0.0/12  (172.16.0.0 - 172.31.255.255)
# 192.168.0.0/16 (192.168.0.0 - 192.168.255.255)


class VpcStack(Stack):
    def __init__(
        self, scope: Construct, construct_id: str, config: dict, **kwargs
    ) -> None:
        super().__init__(scope, construct_id, **kwargs)
        self.stack_config = config["vpc_cdk_stack"]

        # VPC
        self.vpc = ec2.Vpc(
            self,
            self.stack_config["vpc_name"],
            ip_addresses=ec2.IpAddresses.cidr(self.stack_config["cidr"]),
            max_azs=3,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    # subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24,
                ),
            ],
        )

        self.lambda_security_group = ec2.SecurityGroup(
            self,
            "InvokeYOLOLambdaSecurityGroup",
            vpc=self.vpc,
            description="Security group for Lambda functions",
            allow_all_outbound=True,
        )

        self.selected_subnet = self.vpc.public_subnets[0]

        # Create S3 Gateway Endpoint
        self.s3_gateway_endpoint = ec2.GatewayVpcEndpoint(
            self,
            "S3GatewayEndpoint",
            vpc=self.vpc,
            service=ec2.GatewayVpcEndpointAwsService.S3,
            subnets=[
                ec2.SubnetSelection(subnets=[self.selected_subnet]),
            ],
        )

        CfnOutput(self, "VpcId", value=self.vpc.vpc_id, export_name="shared-vpc-id")

        CfnOutput(
            self,
            "SubnetId",
            value=self.vpc.public_subnets[0].subnet_id,
            description="Public Subnet ID where ENI is created",
        )

        CfnOutput(
            self,
            "S3GatewayEndpointId",
            value=self.s3_gateway_endpoint.vpc_endpoint_id,
            description="S3 Gateway Endpoint ID",
        )
