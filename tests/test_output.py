from datetime import date
import unicodedata
import functools

from today.task import Task
from today.output import task_should_be_displayed, task_summary, task_sorter


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

        # Task with only reminder date
        task = Task(reminder_date=date(2022, 1, 5), title="Task 1")
        assert task_summary(task, today=date(2022, 1, 5)) == \
               "[**Reminder today**]"
        assert task_summary(task, today=date(2022, 1, 4)) == \
               "[Reminder in 1 day]"
        assert task_summary(task, today=date(2022, 1, 1)) == \
               "[Reminder in 4 days]"
        assert task_summary(task, today=date(2022, 1, 6)) == \
               "[**Reminder 1 day ago**]"
        assert task_summary(task, today=date(2022, 1, 10)) == \
               "[**Reminder 5 days ago**]"

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

    def test_task_sorting(self) -> None:
        today = date(2022, 1, 6)
        due_1_5 = Task(title="due_1_5", due_date=date(2022, 1, 5))
        remind_1_5 = Task(title="remind_1_5", reminder_date=date(2022, 1, 5))
        due_1_6 = Task(title="due_1_6", due_date=date(2022, 1, 6))
        remind_1_6 = Task(title="remind_1_6", reminder_date=date(2022, 1, 6))
        due_1_7 = Task(title="due_1_7", due_date=date(2022, 1, 7))

        # sort by:
        # 1. heading path (easy)

        # 2. past due tasks
        # 3. tasks due today
        # Task due at 1/5 is past due vs the task due at 1/6 (due today)
        assert sorted([due_1_5, due_1_6], key=functools.partial(task_sorter, today=today)) == \
               [due_1_5, due_1_6]
        assert sorted([due_1_6, due_1_5], key=functools.partial(task_sorter, today=today)) == \
               [due_1_5, due_1_6]

        # 4. tasks with reminders today or in the past
        assert sorted([due_1_6, due_1_5, remind_1_5, remind_1_6], key=functools.partial(task_sorter, today=today)) == \
               [remind_1_5, due_1_5, due_1_6, remind_1_6]
        assert sorted([remind_1_5, remind_1_6], key=functools.partial(task_sorter, today=today)) == \
               [remind_1_5, remind_1_6]

        # 5. tasks with due/reminder dates in the future
        assert sorted([due_1_7, due_1_5, remind_1_5, remind_1_6], key=functools.partial(task_sorter, today=today)) == \
               [remind_1_5, due_1_5, remind_1_6, due_1_7]
