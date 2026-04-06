import logging
import json
import os
from datetime import datetime
from typing import Any, Dict, Optional


class IndustryLogger:
    """
    Structured logger that writes to files named:
        <agent_mode> - <model> - <timestamp>.log

    Usage:
        logger = IndustryLogger()
        logger.configure(agent_mode="agent_v2", model="gpt-4o")
        logger.log_event("AGENT_START", {"input": "..."})
    """

    def __init__(self, name: str = "AI-Lab-Agent", log_dir: str = "logs"):
        self.name = name
        self.log_dir = log_dir
        self._agent_mode: Optional[str] = None
        self._model: Optional[str] = None
        self._file_handler: Optional[logging.FileHandler] = None

        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # Prevent duplicate handlers on re-import
        if not self.logger.handlers:
            console_handler = logging.StreamHandler()
            self.logger.addHandler(console_handler)

        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

    # ------------------------------------------------------------------
    # Configure — sets agent mode + model and creates the log file
    # ------------------------------------------------------------------
    def configure(self, agent_mode: str, model: str):
        """
        Set the agent mode and model name.
        Creates (or switches to) a log file named:
            <agent_mode> - <model> - <YYYY-MM-DD_HH-MM-SS>.log
        """
        self._agent_mode = agent_mode
        self._model = model

        # Remove previous file handler if any
        if self._file_handler and self._file_handler in self.logger.handlers:
            self.logger.removeHandler(self._file_handler)
            self._file_handler.close()

        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{agent_mode} - {model} - {timestamp}.log"
        filepath = os.path.join(self.log_dir, filename)

        self._file_handler = logging.FileHandler(filepath, encoding="utf-8")
        self.logger.addHandler(self._file_handler)

    # ------------------------------------------------------------------
    # Core logging
    # ------------------------------------------------------------------
    def log_event(self, event_type: str, data: Dict[str, Any]):
        """Logs a structured JSON event with agent context."""
        # Auto-configure on first log_event if not yet configured
        if self._file_handler is None:
            mode = data.get("agent_mode") or self._agent_mode or "unknown"
            model = data.get("model") or self._model or "unknown"
            self.configure(agent_mode=mode, model=model)

        payload = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent_mode": self._agent_mode or "unknown",
            "model": self._model or "unknown",
            "event": event_type,
            "data": data,
        }
        self.logger.info(json.dumps(payload, ensure_ascii=False))

    def info(self, msg: str):
        self.logger.info(msg)

    def error(self, msg: str, exc_info=True):
        self.logger.error(msg, exc_info=exc_info)


# Global logger instance
logger = IndustryLogger()
