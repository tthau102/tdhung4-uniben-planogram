import boto3
import json
from datetime import datetime
from decimal import Decimal
from typing import Dict, Any, Optional, Union
import uuid


class DynamoDBWriter:
    def __init__(self, table_name: str, region_name: str = "us-east-1"):
        """
        Khởi tạo DynamoDB writer

        Args:
            table_name: Tên table DynamoDB
            region_name: AWS region (mặc định us-east-1)
        """
        self.dynamodb = boto3.resource("dynamodb", region_name=region_name)
        self.table = self.dynamodb.Table(table_name)
        self.table_name = table_name

    def _convert_to_dynamodb_format(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Chuyển đổi dữ liệu sang format phù hợp với DynamoDB
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
        Ghi một item vào DynamoDB

        Args:
            item_data: Dictionary chứa dữ liệu item

        Returns:
            bool: True nếu thành công, False nếu thất bại
        """
        try:
            # Chuyển đổi dữ liệu
            converted_data = self._convert_to_dynamodb_format(item_data)

            # Thêm id nếu không có
            if "id" not in converted_data:
                converted_data["id"] = str(uuid.uuid4())

            # Thêm timestamp nếu không có
            if "timestamp" not in converted_data:
                converted_data["timestamp"] = datetime.now().isoformat()

            # Ghi vào DynamoDB
            response = self.table.put_item(Item=converted_data)

            print(f"✅ Đã ghi thành công item với ID: {converted_data['id']}")
            return True

        except Exception as e:
            print(f"❌ Lỗi khi ghi item: {str(e)}")
            return False

    def write_multiple_items(self, items_data: list) -> Dict[str, int]:
        """
        Ghi nhiều items vào DynamoDB bằng batch_writer

        Args:
            items_data: List các dictionary chứa dữ liệu

        Returns:
            Dict với số lượng thành công và thất bại
        """
        success_count = 0
        error_count = 0

        try:
            with self.table.batch_writer() as batch:
                for item in items_data:
                    try:
                        # Chuyển đổi dữ liệu
                        converted_data = self._convert_to_dynamodb_format(item)

                        # Thêm id nếu không có
                        if "id" not in converted_data:
                            converted_data["id"] = str(uuid.uuid4())

                        # Thêm timestamp nếu không có
                        if "timestamp" not in converted_data:
                            converted_data["timestamp"] = datetime.now().isoformat()

                        batch.put_item(Item=converted_data)
                        success_count += 1

                    except Exception as e:
                        print(f"❌ Lỗi khi xử lý item: {str(e)}")
                        error_count += 1

            print(
                f"✅ Hoàn thành batch write: {success_count} thành công, {error_count} lỗi"
            )

        except Exception as e:
            print(f"❌ Lỗi batch write: {str(e)}")
            error_count += len(items_data) - success_count

        return {
            "success": success_count,
            "error": error_count,
            "total": len(items_data),
        }

    def update_item(self, item_id: str, update_data: Dict[str, Any]) -> bool:
        """
        Cập nhật một item trong DynamoDB

        Args:
            item_id: ID của item cần update
            update_data: Dictionary chứa dữ liệu cần update

        Returns:
            bool: True nếu thành công
        """
        try:
            # Chuyển đổi dữ liệu
            converted_data = self._convert_to_dynamodb_format(update_data)

            # Tạo update expression
            update_expression = "SET "
            expression_values = {}

            for key, value in converted_data.items():
                if key != "id":  # Không update primary key
                    update_expression += f"{key} = :{key}, "
                    expression_values[f":{key}"] = value

            update_expression = update_expression.rstrip(", ")

            # Thực hiện update
            response = self.table.update_item(
                Key={"id": item_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values,
                ReturnValues="UPDATED_NEW",
            )

            print(f"✅ Đã update thành công item ID: {item_id}")
            return True

        except Exception as e:
            print(f"❌ Lỗi khi update item: {str(e)}")
            return False


# def example_usage():
#     """Ví dụ cách sử dụng DynamoDBWriter"""

#     # Khởi tạo writer
#     writer = DynamoDBWriter("your-table-name", "us-east-1")

#     # Ví dụ 1: Ghi một item
#     single_item = {
#         "id": "123",
#         "image_name": "product_image_001.jpg",
#         "product_count": {"total": 10, "available": 8},
#         "compliance_assessment": True,
#         "need_review": False,
#         "review_comment": "Sản phẩm đạt chuẩn chất lượng",
#         "s3_url": "https://my-bucket.s3.amazonaws.com/images/product_001.jpg",
#         "timestamp": datetime.now(),
#     }

#     writer.write_single_item(single_item)

#     # Ví dụ 2: Ghi nhiều items
#     multiple_items = [
#         {
#             "image_name": "product_002.jpg",
#             "product_count": {"total": 15, "available": 12},
#             "compliance_assessment": True,
#             "need_review": True,
#             "review_comment": "Cần kiểm tra thêm",
#             "s3_url": "https://my-bucket.s3.amazonaws.com/images/product_002.jpg",
#         },
#         {
#             "image_name": "product_003.jpg",
#             "product_count": {"total": 20, "available": 18},
#             "compliance_assessment": False,
#             "need_review": True,
#             "review_comment": "Không đạt chuẩn an toàn",
#             "s3_url": "https://my-bucket.s3.amazonaws.com/images/product_003.jpg",
#         },
#     ]

#     result = writer.write_multiple_items(multiple_items)
#     print(f"Kết quả batch write: {result}")

#     # Ví dụ 3: Update item
#     update_data = {
#         "compliance_assessment": True,
#         "review_comment": "Đã sửa lỗi, hiện tại đạt chuẩn",
#         "need_review": False,
#     }

#     writer.update_item("123", update_data)

# if __name__ == "__main__":
#     example_usage()
