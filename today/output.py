from datetime import date, timedelta
from typing import Any, List

from today.task import Task


def task_should_be_displayed(task: Task, date_limit: date) -> bool:
    if task.due_date and task.due_date <= date_limit and task.done is False:
        return True
    elif task.reminder_date and task.reminder_date <= date_limit and task.done is False:
        return True
    elif task.subtasks and any([st.due_date and st.due_date <= date_limit and st.done is False for st in task.subtasks]):
        return True
    elif task.subtasks and any([st.reminder_date and st.reminder_date <= date_limit and st.done is False for st in task.subtasks]):
        return True
    else:
        return False


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


def days(days: timedelta) -> str:
    if days.days == 1:
        return f"{days.days} day"
    else:
        return f"{days.days} days"


def date_relative_to_today(d: date, today: date, prefix: str = "") -> str:
    if d < today:
        delta: timedelta = today - d
        return f"**{prefix}{days(delta)} ago**"  # Something already passed, high priority (bold)
    elif d == today:
        return f"**{prefix}today**"  # Something today, high priority (bold)
    else:
        delta_inv: timedelta = d - today
        return f"{prefix}in {days(delta_inv)}"  # Something in the future, low priority


def task_summary(task: Task, today: date) -> str:  # Returns a Markdown string
    if task.due_date:
        due_msg = date_relative_to_today(task.due_date, today, prefix="Due ")
    if task.reminder_date:
        reminder_msg = date_relative_to_today(task.reminder_date, today, prefix="Reminder ")

    if task.reminder_date and not task.due_date:  # Reminder only
        return f"[{reminder_msg}]"
    elif task.due_date and not task.reminder_date:  # Due date only
        return f"[{due_msg}]"
    else:  # Both due and reminder dates
        assert task.due_date
        if task.due_date > today:  # Only show reminder if task is not overdue
            return f"[{reminder_msg}] [{due_msg}]"
        else:
            return f"[{due_msg}]"


def task_details(task: Task, task_id: int, today: date) -> str:  # Returns a Markdown string
    string = ""
    string += f"**Title**: {task.title} (id = `{task_id}`)  \n"
    if task.due_date:
        string += f"**Due date**: {task.due_date} ({date_relative_to_today(task.due_date, today, prefix='Due ')})  \n"
    if task.reminder_date:
        string += f"**Reminder date**: {task.reminder_date} ({date_relative_to_today(task.reminder_date, today, prefix='Reminder ')})  \n"
    if len(task.description) > 0:
        string += f"**Description**:  \n\n"
        string += task.description
    return string
