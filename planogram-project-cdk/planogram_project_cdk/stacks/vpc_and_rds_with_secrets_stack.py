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


class VpcAndRdsWithSecretsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # VPC for RDS
        self.vpc = ec2.Vpc(
            self,
            "planogram-VPC",
            ip_addresses=ec2.IpAddresses.cidr("10.15.0.0/16"),
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

        self.all_subnets = self.vpc.public_subnets + self.vpc.isolated_subnets

        self.database_name = "planogram"
        self.db_instance = rds.DatabaseInstance(
            self,
            "planogram-PostgresDB",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_17_2
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.T3, ec2.InstanceSize.LARGE
            ),
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnets=self.all_subnets  # Use combined subnets
            ),
            allocated_storage=100,
            database_name=self.database_name,
            credentials=rds.Credentials.from_generated_secret("postgres"),
            removal_policy=RemovalPolicy.DESTROY,
        )

        # Create security group for the ENI
        # security_group = ec2.SecurityGroup(
        #     self,
        #     "ENISecurityGroup",
        #     vpc=vpc,
        #     description="Security group for ENI with Elastic IP",
        #     allow_all_outbound=True,
        # )

        # # Add inbound rules as needed
        # security_group.add_ingress_rule(
        #     peer=ec2.Peer.any_ipv4(),
        #     connection=ec2.Port.tcp(22),
        #     description="Allow SSH",
        # )

        # security_group.add_ingress_rule(
        #     peer=ec2.Peer.any_ipv4(),
        #     connection=ec2.Port.tcp(443),
        #     description="Allow HTTPS",
        # )

        # Create Elastic Network Interface in the first public subnet
        print(self.vpc.public_subnets)
        self.selected_subnet = self.vpc.public_subnets[0]

        self.eni = ec2.CfnNetworkInterface(
            self,
            "HungPublicENI",
            subnet_id=self.selected_subnet.subnet_id,
            description="ENI in public subnet with Elastic IP",
            # group_set=[security_group.security_group_id],
            tags=[
                # {"key": "project", "value": "planogram"},
                {"key": "Subnet", "value": self.selected_subnet.subnet_id},
            ],
        )

        # Create Elastic IP
        self.elastic_ip = ec2.CfnEIP(
            self,
            "ElasticIP",
            domain="vpc",
            tags=[
                {"key": "Name", "value": "ENI-Elastic-IP"},
                {"key": "Purpose", "value": "Public Subnet ENI"},
            ],
        )

        # Associate Elastic IP with the ENI
        self.eip_association = ec2.CfnEIPAssociation(
            self,
            "EIPAssociation",
            allocation_id=self.elastic_ip.attr_allocation_id,
            network_interface_id=self.eni.ref,
        )

        CfnOutput(
            self, "ExportedVpcId", value=self.vpc.vpc_id, export_name="shared-vpc-id"
        )

        CfnOutput(
            self,
            "ExportedRdsEndpoint",
            value=self.db_instance.db_instance_endpoint_address,
            export_name="shared-rds-endpoint",
        )

        CfnOutput(
            self,
            "SecretArn",
            value=self.db_instance.secret.secret_arn,
            description="Complete secret with all connection details",
        )

        CfnOutput(
            self,
            "ElasticIPAddress",
            value=self.elastic_ip.attr_public_ip,
            description="Elastic IP Address",
        )

        CfnOutput(
            self,
            "ENIId",
            value=self.eni.ref,
            description="Elastic Network Interface ID",
        )

        CfnOutput(
            self,
            "ENIPrivateIP",
            value=self.eni.attr_primary_private_ip_address,
            description="ENI Private IP Address",
        )

        CfnOutput(
            self,
            "SubnetId",
            value=self.vpc.public_subnets[0].subnet_id,
            description="Public Subnet ID where ENI is created",
        )
