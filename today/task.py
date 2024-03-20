from typing import Optional, List, Any
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path


# Some functions to simplify stringifying task descriptions and summaries
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


TaskTitle = str


@dataclass
class DateAttribute:
    created_date: Optional[date] = None
    due_date: Optional[date] = None
    reminder_date: Optional[date] = None
    finished_date: Optional[date] = None

    # today = 3, due_date = 5 (not visible)
    # today = 5, due_date = 5 (visible)
    # today = 3, due_date = 5, lookahead_days = 1 (not visible)
    # today = 3, due_date = 5, lookahead_days = 2 (visible)
    def is_visible(self, today: date, lookahead_days: int) -> bool:
        effective_date = today + timedelta(days=lookahead_days)
        if self.due_date and effective_date >= self.due_date:
            return True
        elif self.reminder_date and effective_date >= self.reminder_date:
            return True
        else:
            return False

    # If this is a subtask and we have the attributes of the parent task,
    # propagate the parent attributes into the subtask
    def merge_attributes(self, parent_attrs: "DateAttribute") -> None:
        if self.created_date is None:
            self.created_date = parent_attrs.created_date
        if self.due_date is None:
            self.due_date = parent_attrs.due_date
        if self.reminder_date is None:
            self.reminder_date = parent_attrs.reminder_date
        if self.finished_date is None:
            self.finished_date = parent_attrs.finished_date

    def summary(self, today: date) -> str:
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

    def details(self, today: date) -> str:
        string = ""
        if self.due_date:
            string += f"**Due date**: {self.due_date} ({date_relative_to_today(self.due_date, today, prefix='Due ')})  \n"
        if self.reminder_date:
            string += f"**Reminder date**: {self.reminder_date} ({date_relative_to_today(self.reminder_date, today, prefix='Reminder ')})  \n"
        return string


@dataclass
class AssignmentAttribute:
    assigned_to: str


@dataclass
class PriorityAttribute:
    # [priority] of 0 is higher than [priority] of 1
    priority: int

    def summary(self) -> str:
        return f"[***Priority*** = {self.priority}]"


@dataclass
class TaskAttributes:
    date_attr: DateAttribute = field(default_factory=lambda: DateAttribute())
    assn_attr: Optional[AssignmentAttribute] = None
    priority_attr: Optional[PriorityAttribute] = None

    def is_visible(self, today: date, lookahead_days: int) -> bool:
        raise NotImplementedError()

    def merge_attributes(self, parent_attrs: "TaskAttributes") -> None:
        # TODO: are there other attributes to merge? (priority or assignment)
        self.date_attr.merge_attributes(parent_attrs.date_attr)


@dataclass
class Task:
    path: List[str] = field(default_factory=lambda: [])
    title: str = ""
    done: bool = False
    description: str = ""  # A Markdown string with the task description
    subtasks: List["Task"] = field(default_factory=lambda: [])
    attrs: TaskAttributes = field(default_factory=lambda: TaskAttributes())
    file_path: Path = Path.cwd()
    line_number: int = 0

    # A task should be displayed if it has a reminder or due date that is today or has passed
    # If a task is already done then it should not be displayed no matter what
    def is_displayed(self, today: date, lookahead_days: int = 0) -> bool:
        task_visible = self.attrs.date_attr.is_visible(today, lookahead_days)
        subtasks_visible = any(
            [t.is_displayed(today, lookahead_days) for t in self.subtasks]
        )
        return (task_visible or subtasks_visible) and not self.done

    def summary(self, today: date) -> str:  # Returns a Markdown string
        date_summary = self.attrs.date_attr.summary(today)
        pri_summary = (
            (self.attrs.priority_attr.summary() + " ")
            if self.attrs.priority_attr
            else ""
        )
        return pri_summary + date_summary

    def details(self, task_id: int, today: date) -> str:  # Returns a Markdown string
        string = ""
        string += f"**Title**: {self.title} (id = `{task_id}`)  \n"
        if len(self.description) > 0:
            string += "**Description**:  \n\n"
            string += self.description
        return string


# sort by:
# 1. heading path
# 2. past due tasks
# 3. tasks due today
# 4. tasks with reminders today or in the past
# 5. tasks with due/reminder dates in the future
def task_sorter(task: Task, today: date) -> Any:
    keys: List[Any] = []
    keys.append(task.path)
    if task.attrs.date_attr.reminder_date:
        keys.append(task.attrs.date_attr.reminder_date - today)
    else:
        keys.append(timedelta(days=0))
    if task.attrs.date_attr.due_date:
        keys.append(task.attrs.date_attr.due_date - today)
    else:
        keys.append(timedelta(days=0))
    return keys
