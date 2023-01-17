import mistune
from mistune import BlockState
from mistune.renderers.markdown import MarkdownRenderer


class TestParser:
    simple_md = """# Tasks

- [ ] Task 1
"""

    def test_roundtrip(self) -> None:
        # Convert Markdown to AST and back to Markdown
        ast_parser = mistune.create_markdown(renderer=None)
        ast = ast_parser(self.simple_md)

        md_renderer = MarkdownRenderer()
        md = md_renderer(ast, BlockState())
        print(md)
        assert md == self.simple_md

    """
    def test_basic_tasks(self) -> None:
        with ASTRenderer() as renderer:
            doc = Document(self.simple_md)
            #print(doc.children[0].children)
            rendered = renderer.render(doc)  # render the AST
            print(rendered)
    """
