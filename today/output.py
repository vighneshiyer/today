from datetime import date, timedelta

from today.task import Task


def task_should_be_displayed(task: Task, date_limit: date) -> bool:
    if task.due_date and task.due_date <= date_limit and task.done is False:
        return True
    elif task.reminder_date and task.reminder_date <= date_limit and task.done is False:
        return True
    else:
        return False


def days(days: timedelta) -> str:
    if days.days == 1:
        return f"{days.days} day"
    else:
        return f"{days.days} days"


def task_summary(task: Task, today: date) -> str:  # Merging markdown with strings is tough
    assert task.due_date is not None
    if task.due_date == today:
        return f"[**Due today**]"
    elif task.due_date > today:
        due_delta: timedelta = task.due_date - today
        if task.reminder_date:
            if task.reminder_date > today:  # Reminder in the future
                reminder_delta: timedelta = task.reminder_date - today
                return f"[Reminder in {days(reminder_delta)}] [Due in {days(due_delta)}]"
            elif task.reminder_date and task.reminder_date == today:
                return f"[**Reminder today**] [Due in {days(due_delta)}]"
            else:
                reminder_delta_inv: timedelta = today - task.reminder_date
                return f"[**Reminder {days(reminder_delta_inv)} ago**] [Due in {days(due_delta)}]"
        else:
            return f"[Due in {days(due_delta)}]"
    else:
        delta: timedelta = today - task.due_date
        return f"[**Due {days(delta)} ago**]"
