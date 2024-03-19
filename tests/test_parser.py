import pytest
from datetime import date

from today.task import DateAttribute, Task, TaskAttributes, date_relative_to_today
from today.parser import (
    parse_heading,
    handle_headings_stack,
    parse_markdown,
    extract_task_attrs,
    parse_task_title,
    Heading,
)


class TestParser:
    today = date.today()

    def test_parse_heading(self) -> None:
        assert parse_heading("# Title") == Heading(1, "Title")
        assert parse_heading("### **title 2**") == Heading(3, "**title 2**")
        with pytest.raises(ValueError):
            parse_heading("bare line")

    def test_handle_headings_stack(self) -> None:
        # Test initial filling
        with pytest.raises(ValueError):
            handle_headings_stack([], "### h3")

        # Test deepening hierarchy
        assert handle_headings_stack([], "# h1") == ["h1"]
        assert handle_headings_stack(["h1", "h2"], "### h3") == ["h1", "h2", "h3"]
        with pytest.raises(ValueError):
            handle_headings_stack(["h1", "h2"], "#### h4")

        # Test flat hierarchy traversal
        assert handle_headings_stack(["h1", "h2"], "## h2prime") == ["h1", "h2prime"]

        # Test pulling out of hierarchy
        assert handle_headings_stack(["h1", "h2"], "# h1prime") == ["h1prime"]
        assert handle_headings_stack(["h1", "h2", "h3"], "## h2prime") == [
            "h1",
            "h2prime",
        ]
        assert handle_headings_stack(["h1", "h2", "h3", "h4"], "## h2prime") == [
            "h1",
            "h2prime",
        ]
        assert handle_headings_stack(["h1", "h2", "h3", "h4"], "# h1prime") == [
            "h1prime"
        ]

    def test_extract_task_attrs(self) -> None:
        # Simple attributes
        attrs, title = extract_task_attrs(
            raw_task_title="[c:3/4/2024] things #tag [d:3/8/2024] [f:t] asdf",
            today=self.today,
        )
        assert attrs.date_attr.created_date == date(2024, 3, 4)
        assert attrs.date_attr.due_date == date(2024, 3, 8)
        assert attrs.date_attr.finished_date == self.today
        assert title == "things #tag asdf"

        # Difficult attributes
        attrs2, title2 = extract_task_attrs(
            raw_task_title="title [d:3/3] [link](http://link.org) [@vighneshiyer] [!2]",
            today=self.today,
        )
        assert attrs2.date_attr.due_date == date(self.today.year, 3, 3)
        assert attrs2.assn_attr
        assert attrs2.assn_attr.assigned_to == "vighneshiyer"
        assert attrs2.priority_attr
        assert attrs2.priority_attr.priority == 2
        assert title2 == "title [link](http://link.org)"

        # No attributes
        attrs3, title3 = extract_task_attrs(
            raw_task_title="things #tag",
            today=self.today,
        )
        assert attrs3.priority_attr is None
        assert attrs3.date_attr == DateAttribute()  # empty attribute class
        assert attrs3.assn_attr is None
        assert title3 == "things #tag"

    def test_parse_task_title(self) -> None:
        assert parse_task_title(
            "[d:1/1/2022] task *title* #tag [c:2/2/2022] other [r:1/4/2022] [f:1/5/2022]",
            today=date.today(),
        ) == Task(
            title="task *title* #tag other",
            attrs=TaskAttributes(
                date_attr=DateAttribute(
                    created_date=date(2022, 2, 2),
                    due_date=date(2022, 1, 1),
                    reminder_date=date(2022, 1, 4),
                    finished_date=date(2022, 1, 5),
                )
            ),
        )
        with pytest.raises(RuntimeError):
            parse_task_title("task [k:1/2/2023]", date.today())
        assert parse_task_title("task [d:t] [r:t]", date.today()) == Task(
            title="task",
            attrs=TaskAttributes(
                date_attr=DateAttribute(
                    due_date=date.today(), reminder_date=date.today()
                )
            ),
        )

    def test_basic_task_parsing(self) -> None:
        assert parse_markdown(["- [ ] Task 1"]) == [
            Task(path=[], title="Task 1", done=False, line_number=1)
        ]
        assert parse_markdown(["# h1", "", "## h2", "", "- [ ] Task 1"]) == [
            Task(path=["h1", "h2"], title="Task 1", done=False, line_number=5)
        ]
        assert parse_markdown(
            ["# h1", "", "## h2", "", "- [ ] Task 1", "## h2prime", "", "- [x] Task 2"]
        ) == [
            Task(path=["h1", "h2"], title="Task 1", done=False, line_number=5),
            Task(path=["h1", "h2prime"], title="Task 2", done=True, line_number=8),
        ]
        tasks_with_desc = """# Tasks

- [ ] Task 1 [d:2/3/2023]

Description for task 1

> quote block
>
> another line

- [x] Task 2
"""
        result = parse_markdown(tasks_with_desc.split("\n"), date.today())
        assert result == [
            Task(
                path=["Tasks"],
                title="Task 1",
                done=False,
                line_number=3,
                description="Description for task 1\n\n> quote block\n>\n> another line",
                attrs=TaskAttributes(DateAttribute(due_date=date(2023, 2, 3))),
            ),
            Task(path=["Tasks"], title="Task 2", done=True, line_number=11),
        ]

    def test_bullet_task_parsing(self) -> None:
        bullet_tasks = """# Tasks
- [ ] Task 1
- [x] Task 2
- [ ] Task 3

- Bullets
    - Nested bullets

- [ ] Task 4
"""
        result = parse_markdown(bullet_tasks.split("\n"), date.today())
        assert result == [
            Task(path=["Tasks"], title="Task 1", done=False, line_number=2),
            Task(path=["Tasks"], title="Task 2", done=True, line_number=3),
            Task(
                path=["Tasks"],
                title="Task 3",
                done=False,
                description="- Bullets\n    - Nested bullets",
                line_number=4,
            ),
            Task(path=["Tasks"], title="Task 4", done=False, line_number=9),
        ]

    def test_subtask_parsing(self) -> None:
        subtasks = """# Tasks

- [ ] Main task [d:1/10/2022] [r:1/3/2022]
    - [ ] Subtask 1 [d:t]
    - [ ] Subtask 2

Description
"""
        today = date.today()
        result = parse_markdown(subtasks.split("\n"), today)
        assert result == [
            Task(
                path=["Tasks"],
                title="Main task",
                done=False,
                line_number=3,
                description="Description",
                attrs=TaskAttributes(
                    DateAttribute(
                        due_date=date(2022, 1, 10), reminder_date=date(2022, 1, 3)
                    )
                ),
                subtasks=[
                    Task(
                        path=["Tasks"],
                        title="Subtask 1",
                        done=False,
                        line_number=4,
                        attrs=TaskAttributes(
                            DateAttribute(
                                due_date=today, reminder_date=date(2022, 1, 3)
                            )
                        ),
                    ),
                    Task(
                        path=["Tasks"],
                        title="Subtask 2",
                        done=False,
                        line_number=5,
                        attrs=TaskAttributes(
                            DateAttribute(
                                due_date=date(2022, 1, 10),
                                reminder_date=date(2022, 1, 3),
                            )
                        ),
                    ),
                ],
            )
        ]
