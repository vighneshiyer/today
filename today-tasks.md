# Today

## TODO

- [x] Capture file names and line numbers
- [x] CLI
- [x] Emit due dates in CLI + how many days have elapsed
- [x] Emit reminder dates in CLI
- [x] Task description in CLI by specifying a task
- [x] Support Markdown in title text
- [x] Make the task description fancier (explicitly state title, due date, reminders, description)
- [x] Sort tasks by heading path and due date criticality (highest priority = beyond due + due today, then reminders sorted by timedelta)
- [x] Links in task title (how can I make this work during emission so they are terminal clickable?)
- [x] Tasks that only have reminders (emphermal tasks) or reminders that are today [r:t] (sticky)
    - If a task only has a due date, then it is simple - only show the task as due when it is due
    - If a task has both due and reminder dates, the due date subsumes the reminder once the task is actually due. While the reminder is active, both the reminder and due dates show up with the task.
    - If a task has only a reminder date, it should be visible via lookahead. Also once the reminder date has passed and the task incomplete, the reminder should still be active.
        - Reminder only tasks are useful for tasks that are never "due" since you can't specify a date ahead of time, rather you just need to be reminded every now and then to check it
- [x] Fix task sorting with more tests
- [x] Subtasks
- [x] Cancelled tasks
- [x] Start CLI
    - ~~use custom argparse Action to parse dates: https://stackoverflow.com/questions/33301000/custom-parsing-function-for-any-number-of-arguments-in-python-argparse~~
    - [x] Unify argument parsing between the 2 programs
    - i3 integration, use pango syntax in the /tmp/task file: https://docs.gtk.org/Pango/pango_markup.html
- [x] Do not display subtasks that are already checked off
- [x] Write quickstart guide / simplify and shorten docs + add ToC
- ~~[ ] Show subtasks that are done in the visible subtasks (with a checkmark)~~ (goes against the way normal tasks work)
- [x] Do some refactoring and cleanup [d:12/24]
- [x] Migrate more code outside the printing logic in cli.py for unit testing [d:12/24]
- [x] Display the task file name when running today (similar to start) [d:12/24]
- [x] Add line number to `start` display of a task [d:2/15/2024]
- [ ] Be able to select a subtask using `start`

### Importance Markers

The idea is that every day there might be 1-3 critical tasks that should be placed at the top no matter what the heading order is.
There should be a way to mark those critical tasks such that they always show up at the top and it makes task selection easy.
Also, the remaining tasks can be displayed in the normal tree form as 'extras' for a given day.
I'm generalizing this into a priority marking system.

- [ ] Importance markers [d:3/12/2024]
  - [x] Rename date_defns to task_attrs
  - [x] Add importance markers parsing
  - [ ] Add new logic to tree printing
  - [ ] Add README docs

### Assignees

- `[@name]` assigns a task to a particular person
- The start and today CLI scripts should take in `--name` and match against all the names
- Another argument should be `--only-mine` to show only tasks specifically assigned to the name, and not also the anon tasks

### Nits

- [ ] Escape the task name and hierarchy names in `start` when emitting the file for i3status
- [ ] Verify that a subtask that is due earlier than the main task shows up at the right time (when the subtask is due or has a reminder, not the main task)
- [ ] Add coverage checker for unit tests
- [ ] Display the task hierarchy when displaying task details
- [ ] Support specifying subtasks in `start` CLI
- [ ] Support Markdown in `start` CLI output (requires parsing inline Markdown and translating to pango)
- [ ] List tasks without reminders / due dates (+ be able to read from a specific Markdown file vs a directory) (to check if I missed adding due dates to something)
- [ ] Add colors for headings / paths / dates
- [ ] Highlight tags
- [ ] Search by tags
- [ ] Use created dates to figure out tasks that been languishing
- [ ] Generalize created/due/reminder/finish dates - lots of duplicated logic
- [ ] Support rendering headings with Markdown (tough to combine Markdown (since it is not necessarily always inline) and Console Markup)

### Recurring tasks

- TBD: more complex recurrence descriptions, maybe use ical recur format string? This implementation also seems brittle and has many caveats - is there a better way?

```markdown
- A task can be made recurring by specifying a `[recur:]` string in the task title.
    - Recurring tasks cannot have any subtasks, but they can have a description
    - Recurring tasks should not be marked complete. They will show up in your daily report and there is a CLI option to mark an instance of the task complete. This completion isn't tracked anywhere explicitly.
    - Recurring tasks disappear after the day they are scheduled. If you forget to finish a recurring task, you must explicitly add an instance of it to a project if you wish to be reminded later.

[ ] Daily journal [recur:daily]
[ ] Weekly tasks [recur:Sunday]
[ ] Monthly tasks [recur:eom]
```

## Markdown Parser

- Python Markdown libraries
    - [Python-Markdown (3.1k)](https://github.com/Python-Markdown/markdown/) - most popular, middling performance, also not precisely CommonMark compliant
    - [mistune (2.2k)](https://github.com/lepture/mistune) - high performance, not precisely CommonMark compliant
      - Easy AST hacking, high perf, new 3.0 release incoming
    - [marko (179)](https://github.com/frostming/marko) - not popular, but claims best CommonMark compliance, middling performance
      - There is no Markdown renderer (for roundtrip)
    - [mistletoe (552)](https://github.com/miyuchina/mistletoe/) - less popular, claims fastest pure Python CommonMark compliance
      - AST hacking is painful, and no Markdown renderer (for roundtrip)
- Decision
  - All these seem to support raw AST dumping mode, which is what I'm looking for
  - **Initial thoughts**: mistletoe seems to be the best balance of performance and compliance and ease of working with the AST representation; mistune is a close second
  - **Update**: mistune is superior. Markdown renderer from AST, easy pure Python AST (just dicts and lists), fast
  - **Further update**: all these libraries are a pain to work with and have very minimal benefit for this project. I just want to parse very specific Markdown features and leave the rest of the document alone, so I have switched to manual and minimal parsing.

## Rich TUI Library

- [rich (41.6k)](https://github.com/Textualize/rich) seems to be the de-facto option
