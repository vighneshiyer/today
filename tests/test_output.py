from datetime import date

from today.task import Task
from today.output import task_should_be_displayed, task_to_string


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

    def test_task_to_string(self) -> None:
        # Task with only a due date
        task = Task(due_date=date(2022, 1, 5), title="Task 1")
        assert task_to_string(task, today=date(2022, 1, 5)) == \
            "Task 1 [Due today]"
        assert task_to_string(task, today=date(2022, 1, 4)) == \
               "Task 1 [Due in 1 day]"
        assert task_to_string(task, today=date(2022, 1, 1)) == \
               "Task 1 [Due in 4 days]"
        assert task_to_string(task, today=date(2022, 1, 6)) == \
               "Task 1 [!!! Due 1 day ago !!!]"
        assert task_to_string(task, today=date(2022, 1, 10)) == \
               "Task 1 [!!! Due 5 days ago !!!]"

        # Task with due and reminder dates
        task = Task(due_date=date(2022, 1, 5), reminder_date=date(2022, 1, 1), title="Task 1")
        assert task_to_string(task, today=date(2022, 1, 5)) == \
               "Task 1 [Due today]"
        assert task_to_string(task, today=date(2022, 1, 4)) == \
               "Task 1 [Reminder 3 days ago] [Due in 1 day]"
        assert task_to_string(task, today=date(2022, 1, 1)) == \
               "Task 1 [Reminder today] [Due in 4 days]"
        assert task_to_string(task, today=date(2021, 12, 31)) == \
               "Task 1 [Reminder in 1 day] [Due in 5 days]"
        assert task_to_string(task, today=date(2022, 1, 6)) == \
               "Task 1 [!!! Due 1 day ago !!!]"
        assert task_to_string(task, today=date(2022, 1, 10)) == \
               "Task 1 [!!! Due 5 days ago !!!]"
