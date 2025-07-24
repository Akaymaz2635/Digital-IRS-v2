# utils/logger.py
import logging
import json
from datetime import datetime


class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        handler = logging.StreamHandler()
        handler.setFormatter(self._get_formatter())
        self.logger.addHandler(handler)

    def _get_formatter(self):
        return logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    def log_operation(self, operation: str, details: Dict[str, Any]):
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "operation": operation,
            "details": details
        }
        self.logger.info(json.dumps(log_data))