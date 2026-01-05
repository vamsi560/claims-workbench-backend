import logging
import sys
import json
from pythonjsonlogger import jsonlogger
from typing import Any, Dict
import re


class PII_PATTERNS:
    EMAIL = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    SSN = r'\b\d{3}-\d{2}-\d{4}\b'
    PHONE = r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b'
    CREDIT_CARD = r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b'


def mask_pii(text: str) -> str:
    if not isinstance(text, str):
        return text

    text = re.sub(PII_PATTERNS.EMAIL, '[EMAIL_REDACTED]', text)
    text = re.sub(PII_PATTERNS.SSN, '[SSN_REDACTED]', text)
    text = re.sub(PII_PATTERNS.PHONE, '[PHONE_REDACTED]', text)
    text = re.sub(PII_PATTERNS.CREDIT_CARD, '[CC_REDACTED]', text)

    return text


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: dict) -> None:
        super().add_fields(log_record, record, message_dict)

        log_record['timestamp'] = self.formatTime(record, self.datefmt)
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['service'] = 'fnol-observability-api'

        if hasattr(record, 'fnol_id'):
            log_record['fnol_id'] = record.fnol_id
        if hasattr(record, 'stage'):
            log_record['stage'] = record.stage
        if hasattr(record, 'prompt_version'):
            log_record['prompt_version'] = record.prompt_version
        if hasattr(record, 'model_name'):
            log_record['model_name'] = record.model_name

        if 'message' in log_record:
            log_record['message'] = mask_pii(str(log_record['message']))


def setup_logging(log_level: str = "INFO") -> logging.Logger:
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, log_level.upper()))

    handler = logging.StreamHandler(sys.stdout)
    formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S'
    )
    handler.setFormatter(formatter)

    logger.handlers.clear()
    logger.addHandler(handler)

    return logger


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
