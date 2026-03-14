from typing import Dict, List, Literal

from pydantic import BaseModel


class PRSummary(BaseModel):
    pr_number: int
    repo_full_name: str
    tldr: str
    changes_by_area: Dict[str, List[str]]
    reviewer_notes: List[str]
    complexity: Literal["simple", "moderate", "complex"]
    files_changed: int
    lines_added: int
    lines_removed: int
