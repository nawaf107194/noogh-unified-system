import re
import json

class DataSanitizer:
    @staticmethod
    def sanitize_string(data: str) -> str:
        """
        Sanitizes a string by removing non-printable characters and encoding special characters.
        """
        return re.sub(r'[^\x20-\x7E]', '', data).encode('ascii', 'ignore').decode()

    @staticmethod
    def sanitize_number(data: int | float) -> int | float:
        """
        Ensures that the number is within a reasonable range.
        """
        if isinstance(data, int):
            return max(min(data, 2147483647), -2147483648)
        elif isinstance(data, float):
            return max(min(data, 1e+38), -1e+38)
        else:
            raise ValueError("Invalid number type")

    @staticmethod
    def sanitize_json(data: str) -> dict:
        """
        Parses a JSON string and returns a dictionary after sanitizing each field.
        """
        try:
            parsed_data = json.loads(data)
            sanitized_data = {}
            for key, value in parsed_data.items():
                if isinstance(value, str):
                    sanitized_data[key] = DataSanitizer.sanitize_string(value)
                elif isinstance(value, (int, float)):
                    sanitized_data[key] = DataSanitizer.sanitize_number(value)
                else:
                    sanitized_data[key] = value
            return sanitized_data
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format")

    @staticmethod
    def sanitize_list(data: list) -> list:
        """
        Sanitizes each element in a list.
        """
        sanitized_list = []
        for item in data:
            if isinstance(item, str):
                sanitized_list.append(DataSanitizer.sanitize_string(item))
            elif isinstance(item, (int, float)):
                sanitized_list.append(DataSanitizer.sanitize_number(item))
            else:
                sanitized_list.append(item)
        return sanitized_list

    @staticmethod
    def sanitize_dict(data: dict) -> dict:
        """
        Sanitizes each value in a dictionary.
        """
        sanitized_dict = {}
        for key, value in data.items():
            if isinstance(value, str):
                sanitized_dict[key] = DataSanitizer.sanitize_string(value)
            elif isinstance(value, (int, float)):
                sanitized_dict[key] = DataSanitizer.sanitize_number(value)
            elif isinstance(value, list):
                sanitized_dict[key] = DataSanitizer.sanitize_list(value)
            elif isinstance(value, dict):
                sanitized_dict[key] = DataSanitizer.sanitize_dict(value)
            else:
                sanitized_dict[key] = value
        return sanitized_dict

    @staticmethod
    def sanitize(data: any) -> any:
        """
        Main method to sanitize any type of input data.
        """
        if isinstance(data, str):
            return DataSanitizer.sanitize_string(data)
        elif isinstance(data, (int, float)):
            return DataSanitizer.sanitize_number(data)
        elif isinstance(data, list):
            return DataSanitizer.sanitize_list(data)
        elif isinstance(data, dict):
            return DataSanitizer.sanitize_dict(data)
        else:
            return data