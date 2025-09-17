"""
커스텀 로그 포맷터들
"""

import logging
import json
from datetime import datetime


class JsonFormatter(logging.Formatter):
    """JSON 형태 로그 포맷터"""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # 예외 정보 추가
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # 추가 컨텍스트 정보
        for attr in ["user_id", "request_id", "endpoint"]:
            if hasattr(record, attr):
                log_entry[attr] = getattr(record, attr)

        return json.dumps(log_entry, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """컬러 콘솔 포맷터"""

    COLORS = {
        'DEBUG': '\033[36m',  # 청록색
        'INFO': '\033[32m',  # 녹색
        'WARNING': '\033[33m',  # 노란색
        'ERROR': '\033[31m',  # 빨간색
        'CRITICAL': '\033[35m',  # 마젠타
        'RESET': '\033[0m'  # 리셋
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']

        formatter = logging.Formatter(
            f"{color}%(asctime)s - %(name)s - %(levelname)s{reset} - %(message)s",
            datefmt="%H:%M:%S"
        )

        return formatter.format(record)