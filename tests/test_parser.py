import mistune
from mistune import BlockState
from mistune.renderers.markdown import MarkdownRenderer

from today.task import parse_markdown, Task


class TestParser:
    simple_md = """# Tasks

- [ ] Task 1

- [ ] Task 2
"""
    ast_parser = mistune.create_markdown(renderer=None)

    def test_roundtrip(self) -> None:
        # Convert Markdown to AST and back to Markdown
        ast = self.ast_parser(self.simple_md)

        md_renderer = MarkdownRenderer()
        md = md_renderer(ast, BlockState())
        assert md == self.simple_md

    def test_basic_task_parsing(self) -> None:
        # Parse an AST to tasks
        ast = self.ast_parser(self.simple_md)
        tasks = parse_markdown(ast)
        assert tasks == [
            Task(path=["Tasks"], title="Task 1", done=False),
            Task(path=["Tasks"], title="Task 2", done=False)
        ]