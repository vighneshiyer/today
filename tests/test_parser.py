import mistune
import pytest

from today.task import parse_markdown, Task, parse_heading, handle_headings_stack, parse_markdown_str


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

    def test_parse_md(self) -> None:
        assert parse_markdown_str(["- [ ] Task 1"]) == [Task(path=[], title="Task 1", done=False)]
        assert parse_markdown_str(["# h1", "", "## h2", "", "- [ ] Task 1"]) == [Task(path=["h1", "h2"], title="Task 1", done=False)]
        assert parse_markdown_str(["# h1", "", "## h2", "", "- [ ] Task 1", "## h2prime", "", "- [x] Task 2"]) == [
            Task(path=["h1", "h2"], title="Task 1", done=False),
            Task(path=["h1", "h2prime"], title="Task 2", done=True),
        ]
        tasks_with_desc = """# Tasks

- [ ] Task 1

Description for task 1

> quote block
>
> another line

- [x] Task 2
"""
        result = parse_markdown_str(tasks_with_desc.split('\n'))
        assert result == [
            Task(path=["Tasks"], title="Task 1", done=False, description="Description for task 1\n\n> quote block\n>\n> another line"),
            Task(path=["Tasks"], title="Task 2", done=True)
        ]

        bullet_tasks = """# Tasks
- [ ] Task 1
- [x] Task 2
- [ ] Task 3

d3 for task 3
"""
        result = parse_markdown_str(bullet_tasks.split('\n'))
        assert result == [
            Task(path=["Tasks"], title="Task 1", done=False),
            Task(path=["Tasks"], title="Task 2", done=True),
            Task(path=["Tasks"], title="Task 3", done=False, description="d3 for task 3"),
        ]