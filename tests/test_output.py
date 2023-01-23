from datetime import date
import unicodedata

from rich.console import Console
from rich.markdown import Markdown

from today.task import Task
from today.output import task_should_be_displayed, task_summary


def remove_control_characters(s):
    return "".join(ch for ch in s if unicodedata.category(ch)[0] != "C")

class TestOutput:
    def test_task_should_be_displayed(self) -> None:
        assert task_should_be_displayed(Task(due_date=date(2022, 1, 5)), date(2022, 1, 4)) is False
        assert task_should_be_displayed(Task(due_date=date(2022, 1, 5)), date(2022, 1, 5)) is True
        assert task_should_be_displayed(Task(due_date=date(2022, 1, 5)), date(2022, 1, 6)) is True
        assert task_should_be_displayed(Task(due_date=date(2022, 1, 5), done=True), date(2022, 1, 6)) is False
        assert task_should_be_displayed(Task(due_date=date(2022, 1, 5), reminder_date=date(2022, 1, 3)), date(2022, 1, 1)) is False
        assert task_should_be_displayed(Task(due_date=date(2022, 1, 5), reminder_date=date(2022, 1, 3)), date(2022, 1, 3)) is True
        assert task_should_be_displayed(Task(due_date=date(2022, 1, 5), reminder_date=date(2022, 1, 3)), date(2022, 1, 4)) is True
        assert task_should_be_displayed(Task(due_date=date(2022, 1, 5), reminder_date=date(2022, 1, 3), done=True), date(2022, 1, 4)) is False

    def test_task_summary(self) -> None:
        # Task with only a due date
        task = Task(due_date=date(2022, 1, 5), title="Task 1")
        assert task_summary(task, today=date(2022, 1, 5)) == \
               "[**Due today**]"
        assert task_summary(task, today=date(2022, 1, 4)) ==\
               "[Due in 1 day]"
        assert task_summary(task, today=date(2022, 1, 1)) == \
               "[Due in 4 days]"
        assert task_summary(task, today=date(2022, 1, 6)) == \
               "[**Due 1 day ago**]"
        assert task_summary(task, today=date(2022, 1, 10)) == \
               "[**Due 5 days ago**]"

        # Task with due and reminder dates
        task = Task(due_date=date(2022, 1, 5), reminder_date=date(2022, 1, 1), title="Task 1")
        assert task_summary(task, today=date(2022, 1, 5)) == \
               "[**Due today**]"
        assert task_summary(task, today=date(2022, 1, 4)) == \
               "[**Reminder 3 days ago**] [Due in 1 day]"
        assert task_summary(task, today=date(2022, 1, 1)) == \
               "[**Reminder today**] [Due in 4 days]"
        assert task_summary(task, today=date(2021, 12, 31)) == \
               "[Reminder in 1 day] [Due in 5 days]"
        assert task_summary(task, today=date(2022, 1, 6)) == \
               "[**Due 1 day ago**]"
        assert task_summary(task, today=date(2022, 1, 10)) == \
               "[**Due 5 days ago**]"
