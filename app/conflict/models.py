from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel


class MergeConflict(BaseModel):
    file_path: str
    conflict_type: Literal["merge", "semantic"]
    branch_a: str
    branch_b: str
    description: str
    severity: Literal["high", "medium", "low"]
    suggested_fix: Optional[str] = None


class ConflictReport(BaseModel):
    repo_full_name: str
    branch_a: str
    branch_b: str
    conflicts: List[MergeConflict]
    summary: str
    timestamp: datetime
    scan_duration_ms: int
