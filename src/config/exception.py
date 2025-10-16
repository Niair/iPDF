# src/config/exception.py
import sys
import inspect
from typing import Any
from src.config.logger import logger

def error_message_details(error: Exception, error_detail: Any = sys) -> str:
    try:
        exc_type, exc_value, exc_tb = error_detail.exc_info()
        if exc_tb:
            tb = exc_tb
            while tb.tb_next:
                tb = tb.tb_next
            file_name = tb.tb_frame.f_code.co_filename
            line_number = tb.tb_lineno
        else:
            frame = inspect.currentframe()
            caller_frame = frame.f_back.f_back if frame and frame.f_back and frame.f_back.f_back else frame
            file_name = caller_frame.f_code.co_filename if caller_frame else "<unknown>"
            line_number = caller_frame.f_lineno if caller_frame else 0

        error_message = (
            f"Error occurred in script [{file_name}] at line [{line_number}]. "
            f"Error message: [{str(error)}]"
        )
        return error_message

    except Exception as e:
        fallback = f"Exception formatting failed: {str(e)} | Original error: {str(error)}"
        try:
            logger.exception("Failed to format exception details.")
        except Exception:
            pass
        return fallback

class CustomException(Exception):
    def __init__(self, error: Exception, error_detail: Any = sys):
        self.original_error = error
        self.details = error_message_details(error, error_detail)
        try:
            logger.error(self.details, exc_info=error_detail.exc_info())
        except Exception:
            print(self.details)
        super().__init__(self.details)

    def __str__(self):
        return self.details
