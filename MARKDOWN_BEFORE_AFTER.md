# Markdown Rendering: Before & After

This document shows the difference between raw markdown display and proper rendering in the TUI.

## Example 1: Task with Bold+Italic

### Before (Raw Markdown)
```
0 - Chores / Cleaning *italics* → ***Wash my car*** [Due today]
```

### After (Rendered)
```
0 - Chores / Cleaning italics → Wash my car [Due today]
                      ^^^^^^    ^^^^^^^^^^^^
                      (italic)  (bold+italic)
```

The task title `***Wash my car***` is now rendered with actual bold and italic styling instead of showing the asterisks.

---

## Example 2: Task with Code Blocks

### Before (Raw Markdown)
```
5 - `Another task` [Due today]
```

### After (Rendered)
```
5 - Another task [Due today]
    ^^^^^^^^^^^^
    (bright white on black background)
```

The backticks are removed and the text is styled as code with distinct coloring.

---

## Example 3: Subtasks with Mixed Formatting

### Before (Raw Markdown)
```
4 - Reminder always today [Reminder today]
        ├── Subtask 1 `with some code` [Reminder today]
        ├── Subtask 2 [Reminder today]
```

### After (Rendered)
```
4 - Reminder always today [Reminder today]
        ├── Subtask 1 with some code [Reminder today]
                      ^^^^^^^^^^^^^^
                      (code styling)
        ├── Subtask 2 [Reminder today]
```

---

## Example 4: Heading with Italic Text

### Before (Raw Markdown)
```
└── Cleaning *italics*
```

### After (Rendered)
```
└── Cleaning italics
             ^^^^^^
             (italic styling)
```

---

## Example 5: Task Detail View with Rich Description

### Before (Raw Markdown)
```
Title: `Another task`
Description:

- Here is a description
    - Some text here too

Some *italics* and **bold** text.

> Also a quote
```

### After (Rendered)
```
Title: Another task
       ^^^^^^^^^^^^
       (code styling)

Description:

  • Here is a description
    - Some text here too

Some italics and bold text.
     ^^^^^^     ^^^^
     (italic)   (bold)

▌ Also a quote
^ (dimmed, with quote marker)
```

---

## Example 6: Priority Task with Complex Path

### Before (Raw Markdown)
```
└── Priority Tasks
    0 - Chores / Cleaning *italics* → ***Wash my car***
```

### After (Rendered)
```
└── Priority Tasks
    0 - Chores / Cleaning italics → Wash my car
                         ^^^^^^    ^^^^^^^^^^^^
                         (italic)  (bold+italic, in cyan path)
```

Note: The markdown is rendered first, then the path coloring is applied, allowing the italic formatting to show through the cyan color.

---

## Technical Details

### ANSI Escape Codes Used

When you see the actual output, it contains ANSI escape sequences:
- `\x1b[1m` = Bold
- `\x1b[3m` = Italic
- `\x1b[97;40m` = Bright white on black (code)
- `\x1b[9m` = Strikethrough
- `\x1b[2m` = Dimmed
- `\x1b[0m` = Reset

### Example Raw Output
```
[1m0[0m - [36mChores / Cleaning [3mitalics[0m[39m → [3m[1mWash my car[0m[0m [[1mDue today[0m]
```

This renders in the terminal as:
- `[1m0[0m` → **0** (bold task number)
- `[36m...[39m` → Path in cyan
- `[3mitalics[0m` → *italics* (within the cyan)
- `[3m[1mWash my car[0m[0m` → ***Wash my car*** (bold+italic)
- `[1mDue today[0m` → **Due today** (bold)

---

## Comparison Summary

| Feature | Before | After |
|---------|--------|-------|
| Task titles | Raw `***text***` | Rendered bold+italic |
| Code blocks | Raw `` `code` `` | Styled code text |
| Italics | Raw `*text*` | Rendered italic |
| Headings | Raw markdown | Rendered formatting |
| Descriptions | Partial rendering | Full markdown support |
| Readability | Cluttered with syntax | Clean, professional |
| Visual hierarchy | Flat | Enhanced with styling |

---

## User Benefits

1. **Cleaner Display**: No more asterisks and backticks cluttering the view
2. **Better Readability**: Styled text is easier to scan visually
3. **Richer Information**: Can use formatting to emphasize important parts
4. **Professional Look**: Terminal output looks polished and intentional
5. **Markdown Compatibility**: Use standard markdown in task files, get nice rendering

---

## Testing

You can verify the rendering yourself:

```bash
# Build the project
cargo build --release

# Test with the example file
./target/release/today --dir example --today 1/10/2022

# View a specific task's details
./target/release/today --dir example --today 1/10/2022 0
```

Compare the output to see how markdown is properly rendered versus shown as raw text.
