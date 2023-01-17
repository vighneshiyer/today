from typing import Optional, List
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Task:
    path: List[str]
    title: str
    created_date: Optional[date]
    reminder_date: Optional[date]
    due_date: Optional[date]
    finished_date: Optional[date]
    done: bool
    subtasks: List["Task"]

def parse_markdown() -> List[Task]:
    pass