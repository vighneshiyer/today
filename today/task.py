from typing import Optional, List, Tuple
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path


@dataclass
class Task:
    path: List[str] = field(default_factory=lambda: [])
    title: str = ""
    done: bool = False
    description: str = ""  # A Markdown string with the task description
    subtasks: List["Task"] = field(default_factory=lambda: [])
    created_date: Optional[date] = None
    reminder_date: Optional[date] = None
    due_date: Optional[date] = None
    finished_date: Optional[date] = None
    file_path: Path = Path.cwd()
    line_number: int = 0
