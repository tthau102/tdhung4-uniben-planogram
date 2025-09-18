#!/usr/bin/env python3
"""
Script to extract actual CloudFormation stack outputs after deployment
and write them to stack-outputs.json with resolved values.
"""

import boto3
import json
import sys
from typing import Dict, Any


def get_stack_outputs(stack_name: str, cf_client) -> Dict[str, Any]:
    """Get outputs from a CloudFormation stack."""
    try:
        response = cf_client.describe_stacks(StackName=stack_name)
        stack = response['Stacks'][0]

        outputs = {}
        if 'Outputs' in stack:
            for output in stack['Outputs']:
                outputs[output['OutputKey']] = output['OutputValue']

        return outputs
    except Exception as e:
        print(f"Error getting outputs for stack {stack_name}: {e}")
        return {}


def main():
    """Extract outputs from all stacks and write to JSON file."""
    # Stack names (adjust these to match your actual stack names)
    stack_names = [
        'VpcAndRdsWithSecretsCdkStack',
        'ExportAnnotationsLambdaCdkStack',
        'CreateTrainingJobLambdaCdkStack',
        'CreateEndpointLambdaCdkStack',
        'InvokeYOLOLambdaCdkStack',
        'DynamoDBCdkStack',
        'S3BucketCdkStack',
        'BedrockInferenceProfileCdkStack'
    ]

    # Initialize CloudFormation client
    cf_client = boto3.client('cloudformation')

    all_outputs = {}

    print("Extracting outputs from CloudFormation stacks...")

    for stack_name in stack_names:
        print(f"Getting outputs from {stack_name}...")
        outputs = get_stack_outputs(stack_name, cf_client)
        if outputs:
            all_outputs[stack_name] = outputs
        else:
            print(f"No outputs found for {stack_name}")

    # Write to JSON file
    output_file = 'stack-outputs.json'
    with open(output_file, 'w') as f:
        json.dump(all_outputs, f, indent=2)

    print(f"Successfully wrote resolved outputs to {output_file}")

    # Print summary
    print("\nSummary of extracted outputs:")
    for stack_name, outputs in all_outputs.items():
        print(f"  {stack_name}: {len(outputs)} outputs")


if __name__ == "__main__":
    main()