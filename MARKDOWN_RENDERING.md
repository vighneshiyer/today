# Markdown Rendering in Today

The Rust version of `today` includes full markdown rendering support for task titles, descriptions, and headings.

## Supported Markdown Elements

### Inline Formatting

| Markdown | Rendering | Example |
|----------|-----------|---------|
| `**bold**` | Bold text | **bold text** |
| `*italic*` | Italic text | *italic text* |
| `***bold+italic***` | Bold and italic | ***bold italic*** |
| `` `code` `` | Code (bright white on black) | `code snippet` |
| `~~strikethrough~~` | Strikethrough with dimmed color | ~~cancelled~~ |

### Block Elements (in descriptions)

| Markdown | Rendering |
|----------|-----------|
| `- bullet` | Bullet points with • symbol |
| `> quote` | Quote blocks with ▌ prefix and dimmed styling |
| Nested bullets | Properly indented sub-bullets |

## Where Markdown is Rendered

### ✅ Task Titles
```markdown
- [ ] ***Important*** task [d:t]
- [ ] Task with `code` in title
- [ ] *Italic* and **bold** text
```

All of these render with proper styling in the task list.

### ✅ Task Descriptions
```markdown
- [ ] A task [d:t]

This description has *italic* and **bold** text.

- Bullet points
    - Nested bullets

> Quoted text
```

Descriptions render with full markdown support.

### ✅ Subtask Titles
```markdown
- [ ] Main task [d:t]
    - [ ] Subtask with `code`
    - [ ] Another with **bold**
```

Subtasks render markdown in their titles.

### ✅ Heading Names
```markdown
## Chores *italics*
```

Heading names in the tree view render markdown formatting.

### ✅ Date Summaries
The bold text in date summaries like `**Due today**` and `**Reminder 3 days ago**` is rendered correctly.

## Implementation

The markdown rendering is implemented in `src/markdown.rs` with two main functions:

1. **`render_markdown(text: &str) -> String`**
   - Renders inline markdown elements (bold, italic, code, strikethrough)
   - Used for task titles, summaries, and single-line text
   - Processes patterns in order: bold+italic, bold, italic, code, strikethrough

2. **`render_markdown_detail(text: &str) -> String`**
   - Renders both inline and block elements
   - Used for task descriptions and detailed views
   - Handles bullets, quotes, nested structures, and header lines

## ANSI Color Codes Used

| Style | ANSI Code | Color/Effect |
|-------|-----------|--------------|
| Bold | `\x1b[1m` | Bright/bold text |
| Italic | `\x1b[3m` | Italic text |
| Code | `\x1b[97;40m` | Bright white on black |
| Strikethrough | `\x1b[9m` | Crossed out |
| Dimmed | `\x1b[2m` | Less intense |
| Cyan | `\x1b[36m` | Cyan (for paths) |
| Reset | `\x1b[0m` | Reset to default |

## Examples

### Task List View
```
Tasks for today (2022-01-10)
└── Priority Tasks
    0 - Chores / Cleaning italics → Wash my car [Due today] (chores.md:6)
                          ^^^^^^    ^^^^^^^^^^^^
                          italic    bold+italic

└── Chores (chores.md)
    └── Cleaning italics
                 ^^^^^^
                 italic
        ├── 5 - Another task [Due today] (chores.md:8)
                ^^^^^^^^^^^^
                code block styling
        └── 6 - Subtask 1 with some code [Reminder today]
                          ^^^^^^^^^^^^^
                          code block styling
```

### Detail View
```
Title: Wash my car
       ^^^^^^^^^^^^
       bold+italic

Description:

  • Here is a description
    - Some text here too

Some italics and bold text.
     ^^^^^^^     ^^^^
     italic      bold

▌ Also a quote
^
dimmed quote block
```

## Testing

The markdown module includes comprehensive unit tests:
- `test_bold()` - Tests **bold** rendering
- `test_italic()` - Tests *italic* rendering
- `test_bold_italic()` - Tests ***bold italic*** rendering
- `test_code()` - Tests `code` rendering
- `test_strikethrough()` - Tests ~~strikethrough~~ rendering
- `test_mixed()` - Tests multiple styles together

Run tests with:
```bash
cargo test
```

## Performance

Markdown rendering uses compiled regex patterns (via `OnceLock`) that are initialized once and reused:
- Pattern compilation happens only once per program run
- Rendering is fast enough to not impact CLI responsiveness
- No noticeable delay even with hundreds of tasks

## Comparison with Python Version

The Python version using `rich` library also rendered some markdown, but:
- The Rust version has explicit control over ANSI codes
- More lightweight than rich (no terminal detection overhead)
- Consistent styling across all platforms
- Better control over color combinations

## Future Enhancements

Potential improvements:
- Support for markdown links with clickable URLs (terminal dependent)
- Support for inline images as ASCII art or file references
- Configurable color themes
- Markdown tables in descriptions
