from __future__ import annotations

from pathlib import Path

from core.logger import get_logger
from src.api.contracts import MessageRequest, MessageResponse, SkillRunRequest, SkillRunResponse
from src.factory import NexusFactory

logger = get_logger(__name__)


class SkillService:
    """Service wrapper that can be reused by CLI, web API, or worker jobs."""

    def __init__(self, factory: NexusFactory | None = None):
        self.factory = factory or NexusFactory()

    def run(self, request: SkillRunRequest) -> SkillRunResponse:
        factory = self.factory
        try:
            if request.working_dir:
                # Sanitize path: remove quotes and normalize separators
                sanitized_path = (
                    request.working_dir.strip()
                    .strip('"\'')  # Remove leading/trailing quotes
                    .replace('\\', '/')  # Normalize backslashes to forward slashes
                )
                logger.info("Using custom working directory", extra={"working_dir": sanitized_path})
                factory = NexusFactory(workspace_root=Path(sanitized_path).resolve())
            
            logger.info("Executing skill", extra={"skill_key": request.skill_key, "prompt_length": len(request.prompt)})
            result = factory.run_skill(prompt=request.prompt, skill_key=request.skill_key)
            
            logger.info("Skill executed successfully", extra={
                "skill_key": result.matched_skill,
                "confidence": result.confidence,
                "mode": result.mode
            })
            
            return SkillRunResponse(
                matched_skill=result.matched_skill,
                confidence=result.confidence,
                mode=result.mode,
                output=result.output,
                assumptions=result.assumptions,
                issues=result.issues,
                artifacts=result.artifacts,
            )
        except Exception as e:
            logger.error("Error during skill execution", extra={"error": str(e), "skill_key": request.skill_key}, exc_info=True)
            raise

    def message(self, request: MessageRequest) -> MessageResponse:
        factory = self.factory
        try:
            if request.working_dir:
                sanitized_path = (
                    request.working_dir.strip()
                    .strip('"\'')
                    .replace('\\', '/')
                )
                logger.info("Using custom working directory", extra={"working_dir": sanitized_path})
                factory = NexusFactory(workspace_root=Path(sanitized_path).resolve())

            logger.info(
                "Executing managed message",
                extra={"channel": request.channel, "skill_key": request.skill_key, "prompt_length": len(request.prompt)},
            )
            result = factory.handle_message(
                prompt=request.prompt,
                skill_key=request.skill_key,
                channel=request.channel,
            )

            matched_skill = result.payload.get("matched_skill") or None
            confidence_raw = result.payload.get("confidence")
            confidence = float(confidence_raw) if confidence_raw else 0.0

            return MessageResponse(
                route=result.mode,
                output=result.summary,
                matched_skill=matched_skill,
                confidence=confidence,
                artifacts={k: v for k, v in result.payload.items() if k not in {"matched_skill", "confidence"}},
            )
        except Exception as e:
            logger.error("Error during managed message execution", extra={"error": str(e)}, exc_info=True)
            raise
