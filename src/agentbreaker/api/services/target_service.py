"""Target configuration and live connectivity verification service."""

import time
from typing import Any

from pydantic import SecretStr

from agentbreaker.api.exceptions import ResourceNotFoundError, SecurityValidationError
from agentbreaker.api.schemas.requests import TargetCreateRequest, TargetUpdateRequest
from agentbreaker.api.schemas.responses import (
    TargetResponseModel,
    TargetTestResponse,
    TargetValidationResponse,
)
from agentbreaker.cli.output import mask_secret
from agentbreaker.cli.storage import StorageManager, storage
from agentbreaker.connectors.factory import get_connector
from agentbreaker.schemas.target import TargetConfig


class TargetService:
    """Service managing target endpoint configurations and health tests."""

    def __init__(self, storage_manager: StorageManager | None = None) -> None:
        self.storage = storage_manager or storage

    def _to_response_model(self, target_id: str, cfg: TargetConfig) -> TargetResponseModel:
        """Convert a TargetConfig into a strictly sanitized TargetResponseModel."""
        raw_key = cfg.api_key.get_secret_value() if cfg.api_key else None
        masked_key = mask_secret(raw_key) if raw_key else None
        header_keys = sorted(cfg.custom_headers.keys())

        return TargetResponseModel(
            target_id=target_id,
            endpoint_url=str(cfg.endpoint_url),
            target_type=cfg.target_type,
            model_name=cfg.model_name,
            api_key_masked=masked_key,
            headers_keys=header_keys,
            timeout_seconds=cfg.timeout_seconds,
            max_concurrency=cfg.max_concurrency,
            max_retries=cfg.max_retries,
            allow_redirects=False,
        )

    def list_targets(self) -> list[TargetResponseModel]:
        """List all provisioned targets in local storage with credentials masked."""
        targets: list[TargetResponseModel] = []
        for t_id in self.storage.list_targets():
            cfg = self.storage.get_target(t_id)
            if cfg:
                targets.append(self._to_response_model(t_id, cfg))
        return targets

    def get_target(self, target_id: str) -> TargetResponseModel:
        """Retrieve a specific target by identifier with credentials masked."""
        cfg = self.storage.get_target(target_id)
        if not cfg:
            raise ResourceNotFoundError(f"Target '{target_id}' not found.")
        return self._to_response_model(target_id, cfg)

    def create_target(self, req: TargetCreateRequest) -> TargetResponseModel:
        """Validate and persist a new target configuration in local storage."""
        if self.storage.get_target(req.target_id):
            raise SecurityValidationError(f"Target '{req.target_id}' already exists.")

        try:
            # Build TargetConfig directly to run strict Pydantic URL & SSRF validators
            cfg_dict: dict[str, Any] = {
                "endpoint_url": req.endpoint_url,
                "target_type": req.target_type,
                "model_name": req.model_name,
                "timeout_seconds": req.timeout_seconds,
                "max_concurrency": req.max_concurrency,
                "max_retries": req.max_retries,
            }
            if req.api_key:
                cfg_dict["api_key"] = SecretStr(req.api_key)
            if req.headers:
                cfg_dict["custom_headers"] = req.headers

            target_cfg = TargetConfig.model_validate(cfg_dict)
        except Exception as err:
            raise SecurityValidationError(f"Invalid target configuration: {err}") from err

        self.storage.save_target(req.target_id, target_cfg)
        return self._to_response_model(req.target_id, target_cfg)

    def update_target(self, target_id: str, req: TargetUpdateRequest) -> TargetResponseModel:
        """Update an existing target configuration."""
        existing = self.storage.get_target(target_id)
        if not existing:
            raise ResourceNotFoundError(f"Target '{target_id}' not found.")

        data = existing.model_dump()
        update_data = req.model_dump(exclude_unset=True)

        for k, v in update_data.items():
            if k == "api_key" and v is not None:
                data[k] = SecretStr(v)
            elif k == "headers" and v is not None:
                data["custom_headers"] = v
            elif v is not None:
                data[k] = v

        try:
            updated_cfg = TargetConfig.model_validate(data)
        except Exception as err:
            raise SecurityValidationError(f"Invalid target update: {err}") from err

        self.storage.save_target(target_id, updated_cfg)
        return self._to_response_model(target_id, updated_cfg)

    def delete_target(self, target_id: str) -> None:
        """Remove a target configuration from storage."""
        if not self.storage.get_target(target_id):
            raise ResourceNotFoundError(f"Target '{target_id}' not found.")
        self.storage.delete_target(target_id)

    def validate_target(self, target_id: str) -> TargetValidationResponse:
        """Perform static configuration and boundary validation."""
        cfg = self.storage.get_target(target_id)
        if not cfg:
            raise ResourceNotFoundError(f"Target '{target_id}' not found.")

        errors: list[str] = []
        warnings: list[str] = []

        if not str(cfg.endpoint_url).startswith(("http://", "https://")):
            errors.append("Endpoint URL must use http:// or https:// scheme.")

        if cfg.timeout_seconds > 60:
            warnings.append("High timeout (>60s) may cause slow assessment runs.")

        if cfg.max_concurrency > 10:
            warnings.append("High concurrency (>10) may trigger target rate limits.")

        return TargetValidationResponse(
            valid=len(errors) == 0,
            target_id=target_id,
            errors=errors,
            warnings=warnings,
        )

    async def test_target_connection(self, target_id: str) -> TargetTestResponse:
        """Perform non-destructive connectivity check against target endpoint."""
        cfg = self.storage.get_target(target_id)
        if not cfg:
            raise ResourceNotFoundError(f"Target '{target_id}' not found.")

        connector = get_connector(cfg)
        start_t = time.perf_counter()

        try:
            resp = await connector.send_prompt("Hello. Ping diagnostic probe.")
            elapsed_ms = round((time.perf_counter() - start_t) * 1000.0, 1)

            if resp.is_error:
                return TargetTestResponse(
                    connected=False,
                    target_id=target_id,
                    status_code=resp.status_code,
                    latency_ms=elapsed_ms,
                    message=f"Target returned error: {resp.error_message}",
                )

            return TargetTestResponse(
                connected=True,
                target_id=target_id,
                status_code=resp.status_code or 200,
                latency_ms=elapsed_ms,
                message="Target connection and test probe succeeded.",
            )
        except Exception as err:
            elapsed_ms = round((time.perf_counter() - start_t) * 1000.0, 1)
            return TargetTestResponse(
                connected=False,
                target_id=target_id,
                status_code=None,
                latency_ms=elapsed_ms,
                message=f"Target connection failed: {err}",
            )
        finally:
            await connector.close()


target_service = TargetService()
