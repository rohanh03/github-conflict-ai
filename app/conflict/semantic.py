from __future__ import annotations

import json
import logging

from app.conflict.models import MergeConflict
from app.llm.base import LLMClient
from app.llm.prompts import CONFLICT_ANALYSIS_SYSTEM, CONFLICT_ANALYSIS_USER
from app.utils.git_ops import truncate_diff

logger = logging.getLogger(__name__)


async def detect_semantic_conflicts(
    llm: LLMClient,
    branch_a: str,
    branch_b: str,
    diff_a: str,
    diff_b: str,
    max_diff_lines: int = 4000,
) -> list[MergeConflict]:
    """Use LLM to detect logical/semantic conflicts between two branch diffs."""
    diff_a_truncated = truncate_diff(diff_a, max_diff_lines // 2)
    diff_b_truncated = truncate_diff(diff_b, max_diff_lines // 2)

    user_prompt = CONFLICT_ANALYSIS_USER.format(
        branch_a=branch_a,
        branch_b=branch_b,
        diff_a=diff_a_truncated,
        diff_b=diff_b_truncated,
    )

    try:
        response = await llm.complete(CONFLICT_ANALYSIS_SYSTEM, user_prompt)
        # Parse JSON from response (handle markdown code blocks)
        json_str = response
        if "```json" in json_str:
            json_str = json_str.split("```json")[1].split("```")[0]
        elif "```" in json_str:
            json_str = json_str.split("```")[1].split("```")[0]

        data = json.loads(json_str.strip())
        conflicts = []
        for c in data.get("conflicts", []):
            conflicts.append(
                MergeConflict(
                    file_path=c.get("file_path", "unknown"),
                    conflict_type="semantic",
                    branch_a=branch_a,
                    branch_b=branch_b,
                    description=c.get("description", ""),
                    severity=c.get("severity", "medium"),
                    suggested_fix=c.get("suggested_fix"),
                )
            )
        logger.info("LLM found %d semantic conflicts", len(conflicts))
        return conflicts

    except (json.JSONDecodeError, KeyError) as e:
        logger.warning("Failed to parse LLM conflict response: %s", e)
        return []
    except Exception:
        logger.exception("LLM semantic analysis failed")
        return []
