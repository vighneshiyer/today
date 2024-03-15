from typing import Optional, List, Any
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path


def date_relative_to_today(d: date, today: date, prefix: str = "") -> str:
    if d < today:
        delta: timedelta = today - d
        return f"**{prefix}{days(delta)} ago**"  # Something already passed, high priority (bold)
    elif d == today:
        return f"**{prefix}today**"  # Something today, high priority (bold)
    else:
        delta_inv: timedelta = d - today
        return f"{prefix}in {days(delta_inv)}"  # Something in the future, low priority


def days(days: timedelta) -> str:
    if days.days == 1:
        return f"{days.days} day"
    else:
        return f"{days.days} days"


@dataclass
class Heading:
    level: int
    name: str


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

    def is_displayed(self, date_limit: date) -> bool:
        if self.due_date and self.due_date <= date_limit and self.done is False:
            return True
        elif (
            self.reminder_date
            and self.reminder_date <= date_limit
            and self.done is False
        ):
            return True
        elif self.subtasks and any(
            [
                st.due_date and st.due_date <= date_limit and st.done is False
                for st in self.subtasks
            ]
        ):
            return True
        elif self.subtasks and any(
            [
                st.reminder_date and st.reminder_date <= date_limit and st.done is False
                for st in self.subtasks
            ]
        ):
            return True
        else:
            return False

    def summary(self, today: date) -> str:  # Returns a Markdown string
        reminder_msg: Optional[str] = None
        due_msg: Optional[str] = None
        if self.due_date:
            due_msg = date_relative_to_today(self.due_date, today, prefix="Due ")
        if self.reminder_date:
            reminder_msg = date_relative_to_today(
                self.reminder_date, today, prefix="Reminder "
            )

        if self.reminder_date and not self.due_date:  # Reminder only
            assert reminder_msg
            return f"[{reminder_msg}]"
        elif self.due_date and not self.reminder_date:  # Due date only
            assert due_msg
            return f"[{due_msg}]"
        else:  # Both due and reminder dates
            assert reminder_msg and due_msg
            assert self.due_date and self.reminder_date
            if self.due_date > today:  # Only show reminder if task is not overdue
                return f"[{reminder_msg}] [{due_msg}]"
            else:
                return f"[{due_msg}]"

    def details(self, task_id: int, today: date) -> str:  # Returns a Markdown string
        string = ""
        string += f"**Title**: {self.title} (id = `{task_id}`)  \n"
        if self.due_date:
            string += f"**Due date**: {self.due_date} ({date_relative_to_today(self.due_date, today, prefix='Due ')})  \n"
        if self.reminder_date:
            string += f"**Reminder date**: {self.reminder_date} ({date_relative_to_today(self.reminder_date, today, prefix='Reminder ')})  \n"
        if len(self.description) > 0:
            string += "**Description**:  \n\n"
            string += self.description
        return string


def task_sorter(task: Task, today: date) -> Any:
    keys: List[Any] = []
    keys.append(task.path)
    if task.reminder_date:
        keys.append(task.reminder_date - today)
    else:
        keys.append(timedelta(days=0))
    if task.due_date:
        keys.append(task.due_date - today)
    else:
        keys.append(timedelta(days=0))
    return keys
