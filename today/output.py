from datetime import date, timedelta
from typing import Any, List

from today.task import Task


def task_should_be_displayed(task: Task, date_limit: date) -> bool:
    if task.due_date and task.due_date <= date_limit and task.done is False:
        return True
    elif task.reminder_date and task.reminder_date <= date_limit and task.done is False:
        return True
    else:
        return False


def task_sorter(task: Task, today: date) -> Any:
    # sort by:
    # 1. heading path
    # 2. past due tasks
    # 3. tasks due today
    # 4. tasks with reminders today or in the past
    # 5. tasks with due/reminder dates in the future
    keys: List[Any] = []
    keys.append(task.path)
    if task.due_date:
        keys.append(task.due_date - today)
    else:
        keys.append(0)
    if task.reminder_date:
        keys.append(task.reminder_date - today)
    else:
        keys.append(0)
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
    assert task.due_date is not None
    due_msg = date_relative_to_today(task.due_date, today, prefix="Due ")

    if task.due_date > today:
        if task.reminder_date:
            reminder_msg = date_relative_to_today(task.reminder_date, today, prefix="Reminder ")
            return f"[{reminder_msg}] [{due_msg}]"
        else:
            return f"[{due_msg}]"
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
