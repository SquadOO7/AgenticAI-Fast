import uuid, base64
from config.logger_config import CustomLogger
from dotenv import dotenv_values

ENV = dotenv_values(".env")
LOGS =CustomLogger()


def generate_unique_hash():
    return str(uuid.uuid4())


def dict_to_string(data, indent=0):
    result = ""
    indent_str = " " * indent

    if isinstance(data, dict):
        for key, value in data.items():
            result += f"{indent_str}{key}:\n"
            result += dict_to_string(value, indent + 2)
    elif isinstance(data, list):
        for item in data:
            result += dict_to_string(item, indent)
    else:
        result += f"{indent_str}{data}\n"

    return result


def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
    return encoded_string


class GlobalState:
    def __init__(self):
        self.env = ENV
        self.logs = LOGS
