"""Serialization and formatting helpers for research reports."""

import json
from typing import Any

from pydantic import BaseModel

from agentbreaker.reporting.redaction import redact_dict


def serialize_report_to_json(report_model: BaseModel, indent: int = 2) -> str:
    """Serialize any Pydantic reporting model into a sanitized JSON string."""
    raw_dict = report_model.model_dump(mode="json")
    clean_dict = redact_dict(raw_dict)
    return json.dumps(clean_dict, indent=indent, ensure_ascii=False)


def dict_to_sanitized_json(data: dict[str, Any], indent: int = 2) -> str:
    """Serialize a dictionary into a sanitized JSON string with secret redaction."""
    clean_dict = redact_dict(data)
    return json.dumps(clean_dict, indent=indent, ensure_ascii=False)
