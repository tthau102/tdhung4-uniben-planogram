import boto3
import json
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional, Union
import uuid


class DynamoDBWriter:
    def __init__(self, table_name: str, region_name: str = "us-east-1"):
        """
        Initialize DynamoDB writer

        Args:
            table_name: DynamoDB table name
            region_name: AWS region (default us-east-1)
        """
        self.dynamodb = boto3.resource("dynamodb", region_name=region_name)
        self.table = self.dynamodb.Table(table_name)
        self.table_name = table_name

    def _convert_to_dynamodb_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert data to DynamoDB compatible format
        """
        converted = {}

        for key, value in data.items():
            if value is None:
                continue
            elif isinstance(value, float):
                converted[key] = Decimal(str(value))
            elif isinstance(value, dict):
                converted[key] = json.dumps(value, ensure_ascii=False)
            elif isinstance(value, (list, tuple)):
                converted[key] = json.dumps(value, ensure_ascii=False)
            elif isinstance(value, bool):
                converted[key] = value
            elif isinstance(value, datetime):
                converted[key] = value.isoformat()
            else:
                converted[key] = str(value)

        return converted

    def write_single_item(self, item_data: Dict[str, Any]) -> bool:
        """
        Write a single item to DynamoDB

        Args:
            item_data: Dictionary containing item data

        Returns:
            bool: True if successful, False if failed
        """
        try:
            # Convert data
            converted_data = self._convert_to_dynamodb_format(item_data)

            # Add id if not present
            if "id" not in converted_data:
                converted_data["id"] = str(uuid.uuid4())

            # Add timestamp if not present
            if "timestamp" not in converted_data:
                converted_data["timestamp"] = datetime.now().isoformat()

            # Write to DynamoDB
            response = self.table.put_item(Item=converted_data)

            print(f"Successfully wrote item with ID: {converted_data['id']}")
            return True

        except Exception as e:
            print(f"Error writing item: {str(e)}")
            return False

    def write_multiple_items(self, items_data: list) -> Dict[str, int]:
        """
        Write multiple items to DynamoDB using batch_writer

        Args:
            items_data: List of dictionaries containing data

        Returns:
            Dict with counts of successful and failed operations
        """
        success_count = 0
        error_count = 0

        try:
            with self.table.batch_writer() as batch:
                for item in items_data:
                    try:
                        # Convert data
                        converted_data = self._convert_to_dynamodb_format(item)

                        # Add id if not present
                        if "id" not in converted_data:
                            converted_data["id"] = str(uuid.uuid4())

                        # Add timestamp if not present
                        if "timestamp" not in converted_data:
                            converted_data["timestamp"] = datetime.now().isoformat()

                        batch.put_item(Item=converted_data)
                        success_count += 1

                    except Exception as e:
                        print(f"❌ Error processing item: {str(e)}")
                        error_count += 1

            print(
                f"Completed batch write: {success_count} successful, {error_count} errors"
            )

        except Exception as e:
            print(f"Batch write error: {str(e)}")
            error_count += len(items_data) - success_count

        return {
            "success": success_count,
            "error": error_count,
            "total": len(items_data),
        }

    def update_item(self, item_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Update an item in DynamoDB

        Args:
            item_id: ID of the item to update
            update_data: Dictionary containing data to update

        Returns:
            bool: True if successful
        """
        try:
            # Convert data
            converted_data = self._convert_to_dynamodb_format(update_data)

            # Create update expression
            update_expression = "SET "
            expression_values = {}

            for key, value in converted_data.items():
                if key != "id":  # Don't update primary key
                    update_expression += f"{key} = :{key}, "
                    expression_values[f":{key}"] = value

            update_expression = update_expression.rstrip(", ")

            # Perform update
            response = self.table.update_item(
                Key={"id": item_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values,
                ReturnValues="UPDATED_NEW",
            )

            print(f"Successfully updated item ID: {item_id}")
            return True

        except Exception as e:
            print(f"Error updating item: {str(e)}")
            return False


# def example_usage():
#     """Example usage of DynamoDBWriter"""

#     # Initialize writer
#     writer = DynamoDBWriter("your-table-name", "us-east-1")

#     # Example 1: Write a single item
#     single_item = {
#         "id": "123",
#         "image_name": "product_image_001.jpg",
#         "product_count": {"total": 10, "available": 8},
#         "compliance_assessment": True,
#         "need_review": False,
#         "review_comment": "Product meets quality standards",
#         "s3_url": "https://my-bucket.s3.amazonaws.com/images/product_001.jpg",
#         "timestamp": datetime.now(),
#     }

#     writer.write_single_item(single_item)

#     # Example 2: Write multiple items
#     multiple_items = [
#         {
#             "image_name": "product_002.jpg",
#             "product_count": {"total": 15, "available": 12},
#             "compliance_assessment": True,
#             "need_review": True,
#             "review_comment": "Needs additional inspection",
#             "s3_url": "https://my-bucket.s3.amazonaws.com/images/product_002.jpg",
#         },
#         {
#             "image_name": "product_003.jpg",
#             "product_count": {"total": 20, "available": 18},
#             "compliance_assessment": False,
#             "need_review": True,
#             "review_comment": "Does not meet safety standards",
#             "s3_url": "https://my-bucket.s3.amazonaws.com/images/product_003.jpg",
#         },
#     ]

#     result = writer.write_multiple_items(multiple_items)
#     print(f"Batch write result: {result}")

#     # Example 3: Update item
#     update_data = {
#         "compliance_assessment": True,
#         "review_comment": "Fixed issues, now meets standards",
#         "need_review": False,
#     }

#     writer.update_item("123", update_data)

# if __name__ == "__main__":
#     example_usage()
