use crate::task::{AssignmentAttribute, Heading, PriorityAttribute, Task, TaskAttributes};
use chrono::{NaiveDate, Datelike};
use regex::Regex;
use std::sync::OnceLock;

/// Get the task attribute regex (compiled once)
fn task_attr_regex() -> &'static Regex {
    static REGEX: OnceLock<Regex> = OnceLock::new();
    REGEX.get_or_init(|| Regex::new(r"\[(?P<prefix>(.:|@|!))(?P<value>.*?)\]\s?").unwrap())
}

/// Get the task line regex
fn task_regex() -> &'static Regex {
    static REGEX: OnceLock<Regex> = OnceLock::new();
    REGEX.get_or_init(|| Regex::new(r"^- \[[ xX]\] ").unwrap())
}

/// Get the subtask line regex
fn subtask_regex() -> &'static Regex {
    static REGEX: OnceLock<Regex> = OnceLock::new();
    REGEX.get_or_init(|| Regex::new(r"^[ \t]+- \[[ xX]\] ").unwrap())
}

/// Parse a Markdown heading line
pub fn parse_heading(s: &str) -> Result<Heading, String> {
    let mut level = 0;
    let chars: Vec<char> = s.chars().collect();
    
    for (i, &ch) in chars.iter().enumerate() {
        if ch == '#' {
            level = i + 1;
        } else if ch == ' ' {
            return Ok(Heading {
                level,
                name: s[i + 1..].to_string(),
            });
        } else {
            return Err(format!("Malformed heading: {}", s));
        }
    }
    
    Err("This should never happen".to_string())
}

/// Handle the heading stack when encountering a new heading
pub fn handle_headings_stack(headings_stack: &mut Vec<String>, heading_raw: &str) -> Result<(), String> {
    let heading = parse_heading(heading_raw)?;
    let last_level = headings_stack.len();
    
    if heading.level > last_level {
        if heading.level != last_level + 1 {
            return Err(format!("Heading {:?} nested too deep", heading));
        }
    } else if heading.level == last_level {
        headings_stack.pop();
    } else {
        for _ in 0..(last_level - heading.level + 1) {
            headings_stack.pop();
        }
    }
    
    headings_stack.push(heading.name);
    Ok(())
}

/// Check if a line is a Markdown checkbox and return its status
pub fn md_checkbox(s: &str) -> Option<bool> {
    if s.starts_with("[ ]") {
        Some(false)
    } else if s.starts_with("[x]") || s.starts_with("[X]") {
        Some(true)
    } else {
        None
    }
}

/// Parse and assign a task attribute
pub fn assign_task_attr(
    prefix: &str,
    value: &str,
    task_attr: &mut TaskAttributes,
    today: NaiveDate,
) -> Result<(), String> {
    if prefix == "@" {
        task_attr.assn_attr = Some(AssignmentAttribute {
            assigned_to: value.to_string(),
        });
        Ok(())
    } else if prefix == "!" {
        let priority = value.parse::<i32>()
            .map_err(|_| format!("Invalid priority value: {}", value))?;
        task_attr.priority_attr = Some(PriorityAttribute { priority });
        Ok(())
    } else {
        // Date attribute
        let prefix_char = prefix.chars().next().unwrap();
        let date_value = if value == "t" {
            today
        } else {
            parse_date(value, today)?
        };
        
        match prefix_char {
            'c' => task_attr.date_attr.created_date = Some(date_value),
            'd' => task_attr.date_attr.due_date = Some(date_value),
            'r' => task_attr.date_attr.reminder_date = Some(date_value),
            'f' => task_attr.date_attr.finished_date = Some(date_value),
            _ => return Err(format!("Date attribute prefix '{}' isn't recognized", prefix_char)),
        }
        
        Ok(())
    }
}

/// Parse a date string (M/D/Y or M/D)
fn parse_date(date_str: &str, today: NaiveDate) -> Result<NaiveDate, String> {
    let parts: Vec<&str> = date_str.split('/').collect();
    
    match parts.len() {
        3 => {
            let month = parts[0].parse::<u32>()
                .map_err(|_| format!("Invalid month: {}", parts[0]))?;
            let day = parts[1].parse::<u32>()
                .map_err(|_| format!("Invalid day: {}", parts[1]))?;
            let year = parts[2].parse::<i32>()
                .map_err(|_| format!("Invalid year: {}", parts[2]))?;
            
            NaiveDate::from_ymd_opt(year, month, day)
                .ok_or_else(|| format!("Invalid date: {}/{}/{}", month, day, year))
        }
        2 => {
            let month = parts[0].parse::<u32>()
                .map_err(|_| format!("Invalid month: {}", parts[0]))?;
            let day = parts[1].parse::<u32>()
                .map_err(|_| format!("Invalid day: {}", parts[1]))?;
            
            NaiveDate::from_ymd_opt(today.year(), month, day)
                .ok_or_else(|| format!("Invalid date: {}/{}", month, day))
        }
        _ => Err(format!("Date attribute value '{}' is improperly formatted", date_str)),
    }
}

/// Extract task attributes from a raw task title
pub fn extract_task_attrs(raw_task_title: &str, today: NaiveDate) -> Result<(TaskAttributes, String), String> {
    let mut task_attr = TaskAttributes::default();
    let regex = task_attr_regex();
    
    let matches: Vec<_> = regex.find_iter(raw_task_title).collect();
    
    if matches.is_empty() {
        return Ok((task_attr, raw_task_title.to_string()));
    }
    
    // Parse each attribute
    for cap in regex.captures_iter(raw_task_title) {
        let prefix = cap.name("prefix").unwrap().as_str();
        let value = cap.name("value").unwrap().as_str();
        
        assign_task_attr(prefix, value, &mut task_attr, today)
            .map_err(|e| format!("Error parsing task title '{}': {}", raw_task_title, e))?;
    }
    
    // Remove all attribute matches from the title
    let mut result = String::new();
    let mut last_end = 0;
    
    for m in matches {
        result.push_str(&raw_task_title[last_end..m.start()]);
        last_end = m.end();
    }
    result.push_str(&raw_task_title[last_end..]);
    
    Ok((task_attr, result.trim_end().to_string()))
}

/// Parse a task title line
pub fn parse_task_title(title: &str, today: NaiveDate) -> Result<Task, String> {
    let (attrs, task_title) = extract_task_attrs(title, today)?;
    Ok(Task {
        title: task_title,
        attrs,
        ..Task::default()
    })
}

/// Parse markdown lines into tasks
pub fn parse_markdown(md: &[String], today: NaiveDate) -> Result<Vec<Task>, String> {
    let mut headings_stack: Vec<String> = Vec::new();
    let mut current_task: Option<Task> = None;
    let mut tasks: Vec<Task> = Vec::new();
    
    for (i, line) in md.iter().enumerate() {
        if line.starts_with('#') {
            // This is a heading
            handle_headings_stack(&mut headings_stack, line)?;
            
            // Headings terminate any task being parsed
            if let Some(task) = current_task.take() {
                tasks.push(task);
            }
        } else if task_regex().is_match(line) {
            // This is a task checkbox
            let checkbox_content = &line[2..]; // Skip "- "
            let task_status = md_checkbox(checkbox_content)
                .ok_or_else(|| format!("Malformed Markdown checkbox on line {}: {}", i + 1, line))?;
            
            if let Some(task) = current_task.take() {
                tasks.push(task);
            }
            
            let task_content = &line[6..]; // Skip "- [ ] "
            let mut task = parse_task_title(task_content, today)?;
            task.path = headings_stack.clone();
            task.done = task_status;
            task.line_number = i + 1;
            
            current_task = Some(task);
        } else if let Some(mat) = subtask_regex().find(line) {
            // This is a subtask
            let current = current_task.as_mut()
                .ok_or_else(|| format!("Encountered subtask without a main task on line {}: {}", i + 1, line))?;
            
            let checkbox_start = line.find('[').unwrap();
            let checkbox_content = &line[checkbox_start..];
            let subtask_status = md_checkbox(checkbox_content)
                .ok_or_else(|| format!("Malformed subtask checkbox on line {}: {}", i + 1, line))?;
            
            let subtask_content = &line[mat.end()..];
            let mut subtask = parse_task_title(subtask_content, today)?;
            subtask.path = headings_stack.clone();
            subtask.done = subtask_status;
            subtask.line_number = i + 1;
            subtask.attrs.merge_attributes(&current.attrs);
            
            current.subtasks.push(subtask);
        } else if line.is_empty() && current_task.is_none() {
            continue;
        } else if let Some(task) = current_task.as_mut() {
            // This is part of the description
            if !task.description.is_empty() {
                task.description.push('\n');
            }
            task.description.push_str(line);
        }
    }
    
    if let Some(task) = current_task {
        tasks.push(task);
    }
    
    // Post-process descriptions
    for task in &mut tasks {
        task.description = task.description.trim().to_string();
    }
    
    Ok(tasks)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_parse_heading() {
        assert_eq!(
            parse_heading("# Title").unwrap(),
            Heading { level: 1, name: "Title".to_string() }
        );
        assert_eq!(
            parse_heading("### **title 2**").unwrap(),
            Heading { level: 3, name: "**title 2**".to_string() }
        );
        assert!(parse_heading("bare line").is_err());
    }

    #[test]
    fn test_md_checkbox() {
        assert_eq!(md_checkbox("[ ]"), Some(false));
        assert_eq!(md_checkbox("[x]"), Some(true));
        assert_eq!(md_checkbox("[X]"), Some(true));
        assert_eq!(md_checkbox("invalid"), None);
    }
}
