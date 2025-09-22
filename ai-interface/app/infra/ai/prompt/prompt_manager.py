import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

import yaml
from fastapi import HTTPException
from jinja2 import Template

from app.core.utils.file_path import find_project_root

logger = logging.getLogger(__name__)


class PromptManager:
    def __init__(self):
        project_root = find_project_root()
        if project_root:
            self.prompts_dir = Path(project_root) / "prompts"
        else:
            self.prompts_dir = Path.cwd() / "prompts"

        self._system_prompts: Dict[str, Dict[str, Any]] = {}
        self._last_loaded: Optional[datetime] = None

        self._load_system_prompts()

    def _load_system_prompts(self):
        """시스템 프롬프트 파일들을 로드합니다."""
        system_dir = self.prompts_dir / "system"
        if not system_dir.exists():
            logger.warning(f"System prompts directory not found: {system_dir}")
            return

        loaded_count = 0
        for prompt_file in system_dir.glob("*.yaml"):
            try:
                domain = prompt_file.stem
                with open(prompt_file, 'r', encoding='utf-8') as f:
                    self._system_prompts[domain] = yaml.safe_load(f)
                loaded_count += 1
                logger.debug(f"Loaded prompt for domain: {domain}")
            except Exception as e:
                logger.error(f"Failed to load prompt file {prompt_file}: {e}")

        self._last_loaded = datetime.now()
        logger.info(f"Loaded {loaded_count} system prompts from {system_dir}")

    def get_system_prompt(self, domain: str, parameters: Optional[Dict[str, Any]] = None) -> str:
        """도메인별 시스템 프롬프트를 가져옵니다."""
        validation_result = self.validate_parameters(domain, parameters)

        if not validation_result["valid"]:
            raise HTTPException(400, "잘못된 파라미터 입니다.")

        prompt_config = self._system_prompts[domain]
        template_str = prompt_config.get("template", "")

        if not template_str:
            logger.warning(f"Empty template for domain: {domain}")
            return ""

        if parameters:
            try:
                # Jinja2 템플릿으로 파라미터 렌더링
                template = Template(template_str)
                rendered = template.render(**parameters)
                logger.debug(f"Rendered prompt for domain {domain} with parameters: {list(parameters.keys())}")
                return rendered
            except Exception as e:
                logger.error(f"Failed to render template for domain {domain}: {e}")
                raise ValueError(f"Template rendering failed: {e}")

        return template_str

    def get_prompt_metadata(self, domain: str) -> Dict[str, Any]:
        """프롬프트의 메타데이터를 반환합니다."""
        if domain not in self._system_prompts:
            raise ValueError(f"Domain '{domain}' not found")

        config = self._system_prompts[domain]
        return {
            "name": config.get("name", domain),
            "description": config.get("description", ""),
            "parameters": config.get("parameters", {}),
            "version": config.get("version", "1.0"),
            "last_updated": config.get("last_updated", "unknown")
        }

    def list_available_domains(self) -> List[Dict[str, Any]]:
        """사용 가능한 도메인 목록과 메타데이터를 반환합니다."""
        domains = []
        for domain in self._system_prompts.keys():
            try:
                metadata = self.get_prompt_metadata(domain)
                domains.append({
                    "domain": domain,
                    **metadata
                })
            except Exception as e:
                logger.error(f"Failed to get metadata for domain {domain}: {e}")
                domains.append({
                    "domain": domain,
                    "name": domain,
                    "description": "Error loading metadata",
                    "error": str(e)
                })
        return domains

    def validate_parameters(self, domain: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """파라미터 유효성을 검사합니다."""
        if domain not in self._system_prompts:
            raise ValueError(f"Domain '{domain}' not found")

        config = self._system_prompts[domain]
        param_schema = config.get("parameters", {})

        validation_result = {
            "valid": True,
            "errors": [],
            "warnings": []
        }

        # 필수 파라미터 확인
        required_params = [k for k, v in param_schema.items() if v.get("required", False)]
        for param in required_params:
            if param not in parameters:
                validation_result["valid"] = False
                validation_result["errors"].append(f"Required parameter '{param}' is missing")

        # 타입 확인
        for param_name, param_value in parameters.items():
            if param_name in param_schema:
                expected_type = param_schema[param_name].get("type")
                if expected_type and not isinstance(param_value, eval(expected_type)):
                    validation_result["warnings"].append(
                        f"Parameter '{param_name}' expected type {expected_type}, got {type(param_value).__name__}"
                    )

        return validation_result

    def reload_prompts(self) -> Dict[str, Any]:
        """프롬프트를 다시 로드합니다."""
        old_count = len(self._system_prompts)
        self._system_prompts.clear()
        self._load_system_prompts()
        new_count = len(self._system_prompts)

        return {
            "status": "success",
            "old_count": old_count,
            "new_count": new_count,
            "reloaded_at": self._last_loaded.isoformat() if self._last_loaded else None,
            "domains": list(self._system_prompts.keys())
        }

    def get_template_preview(self, domain: str, sample_parameters: Optional[Dict[str, Any]] = None) -> str:
        """템플릿 미리보기를 제공합니다."""
        if domain not in self._system_prompts:
            raise ValueError(f"Domain '{domain}' not found")

        # 샘플 파라미터가 없으면 기본값 사용
        if sample_parameters is None:
            config = self._system_prompts[domain]
            param_schema = config.get("parameters", {})
            sample_parameters = {}
            for param_name, param_config in param_schema.items():
                sample_parameters[param_name] = param_config.get("example", f"<{param_name}>")

        return self.get_system_prompt(domain, sample_parameters)
