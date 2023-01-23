import pytest
from datetime import date

from today.task import Task
from today.parser import parse_heading, handle_headings_stack, parse_markdown, extract_date_defns,\
    parse_task_title


class TestParser:
    def test_parse_heading(self) -> None:
        assert parse_heading("# Title") == (1, "Title")
        assert parse_heading("### **title 2**") == (3, "**title 2**")
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
        assert handle_headings_stack(["h1", "h2", "h3"], "## h2prime") == ["h1", "h2prime"]
        assert handle_headings_stack(["h1", "h2", "h3", "h4", "h5"], "## h2prime") == ["h1", "h2prime"]
        assert handle_headings_stack(["h1", "h2", "h3", "h4", "h5"], "# h1prime") == ["h1prime"]

    def test_extract_date_defns(self) -> None:
        date_defns, title = extract_date_defns("[c:33] things #tag [d:233] [f:5] asdf [c:99]")
        assert date_defns == ["c:33", "d:233", "f:5", "c:99"]
        assert title == "things #tag asdf"

    def test_parse_task_title(self) -> None:
        assert parse_task_title("[d:1/1/2022] task *title* #tag [c:2/2/2022] other [r:1/4/2022] [f:1/5/2022]", today=date.today()) == \
                Task(title="task *title* #tag other", due_date=date(2022, 1, 1),
                     created_date=date(2022, 2, 2), reminder_date=date(2022, 1, 4), finished_date=date(2022, 1, 5))
        with pytest.raises(ValueError):
            parse_task_title("task [k:1/2/2023]", date.today())
        assert parse_task_title("task [d:t] [r:t]", date.today()) == \
               Task(title="task", due_date=date.today(), reminder_date=date.today())

    def test_basic_task_parsing(self) -> None:
        assert parse_markdown(["- [ ] Task 1"]) == [Task(path=[], title="Task 1", done=False, line_number=1)]
        assert parse_markdown(["# h1", "", "## h2", "", "- [ ] Task 1"]) == [
            Task(path=["h1", "h2"], title="Task 1", done=False, line_number=5)
        ]
        assert parse_markdown(["# h1", "", "## h2", "", "- [ ] Task 1", "## h2prime", "", "- [x] Task 2"]) == [
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
        result = parse_markdown(tasks_with_desc.split('\n'), date.today())
        assert result == [
            Task(path=["Tasks"], title="Task 1", done=False, line_number=3,
                 description="Description for task 1\n\n> quote block\n>\n> another line", due_date=date(2023, 2, 3)),
            Task(path=["Tasks"], title="Task 2", done=True, line_number=11)
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
        result = parse_markdown(bullet_tasks.split('\n'), date.today())
        assert result == [
            Task(path=["Tasks"], title="Task 1", done=False, line_number=2),
            Task(path=["Tasks"], title="Task 2", done=True, line_number=3),
            Task(path=["Tasks"], title="Task 3", done=False, description="- Bullets\n    - Nested bullets", line_number=4),
            Task(path=["Tasks"], title="Task 4", done=False, line_number=9)
        ]
