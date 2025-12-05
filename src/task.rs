use chrono::{NaiveDate, Duration};
use std::path::PathBuf;

/// Represents a Markdown heading with its level and name
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Heading {
    pub level: usize,
    pub name: String,
}

/// Date attributes for a task
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct DateAttribute {
    pub created_date: Option<NaiveDate>,
    pub due_date: Option<NaiveDate>,
    pub reminder_date: Option<NaiveDate>,
    pub finished_date: Option<NaiveDate>,
}

impl DateAttribute {
    /// Check if this task should be visible given today's date and a lookahead
    pub fn is_visible(&self, today: NaiveDate, lookahead_days: i64) -> bool {
        let effective_date = today + Duration::days(lookahead_days);
        
        if let Some(due_date) = self.due_date {
            if effective_date >= due_date {
                return true;
            }
        }
        
        if let Some(reminder_date) = self.reminder_date {
            if effective_date >= reminder_date {
                return true;
            }
        }
        
        false
    }

    /// Merge parent task attributes into subtask (if subtask attributes are None)
    pub fn merge_attributes(&mut self, parent_attrs: &DateAttribute) {
        if self.created_date.is_none() {
            self.created_date = parent_attrs.created_date;
        }
        if self.due_date.is_none() {
            self.due_date = parent_attrs.due_date;
        }
        if self.reminder_date.is_none() {
            self.reminder_date = parent_attrs.reminder_date;
        }
        if self.finished_date.is_none() {
            self.finished_date = parent_attrs.finished_date;
        }
    }

    /// Generate a summary string for display in task list
    pub fn summary(&self, today: NaiveDate) -> String {
        let reminder_msg = self.reminder_date.map(|d| date_relative_to_today(d, today, "Reminder "));
        let due_msg = self.due_date.map(|d| date_relative_to_today(d, today, "Due "));

        match (self.reminder_date, self.due_date, reminder_msg, due_msg) {
            (Some(_), None, Some(r), _) => format!("[{}]", r),
            (None, Some(_), _, Some(d)) => format!("[{}]", d),
            (Some(_reminder), Some(due), Some(r), Some(d)) => {
                if due > today {
                    format!("[{}] [{}]", r, d)
                } else {
                    format!("[{}]", d)
                }
            }
            _ => String::new(),
        }
    }

    /// Generate detailed string for task details view
    pub fn details(&self, today: NaiveDate) -> String {
        let mut result = String::new();
        
        if let Some(due_date) = self.due_date {
            result.push_str(&format!(
                "**Due date**: {} ({})  \n",
                due_date,
                date_relative_to_today(due_date, today, "Due ")
            ));
        }
        
        if let Some(reminder_date) = self.reminder_date {
            result.push_str(&format!(
                "**Reminder date**: {} ({})  \n",
                reminder_date,
                date_relative_to_today(reminder_date, today, "Reminder ")
            ));
        }
        
        result
    }
}

/// Assignment attribute
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct AssignmentAttribute {
    pub assigned_to: String,
}

/// Priority attribute (lower number = higher priority)
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct PriorityAttribute {
    pub priority: i32,
}

impl PriorityAttribute {
    pub fn summary(&self) -> String {
        format!("[***Priority*** = {}]", self.priority)
    }
}

/// All task attributes
#[derive(Debug, Clone, PartialEq, Eq, Default)]
pub struct TaskAttributes {
    pub date_attr: DateAttribute,
    pub assn_attr: Option<AssignmentAttribute>,
    pub priority_attr: Option<PriorityAttribute>,
}

impl TaskAttributes {
    /// Merge parent task attributes into subtask
    pub fn merge_attributes(&mut self, parent_attrs: &TaskAttributes) {
        self.date_attr.merge_attributes(&parent_attrs.date_attr);
    }
}

/// A task with all its metadata
#[derive(Debug, Clone, PartialEq, Eq)]
pub struct Task {
    pub path: Vec<String>,
    pub title: String,
    pub done: bool,
    pub description: String,
    pub subtasks: Vec<Task>,
    pub attrs: TaskAttributes,
    pub file_path: PathBuf,
    pub line_number: usize,
}

impl Default for Task {
    fn default() -> Self {
        Self {
            path: Vec::new(),
            title: String::new(),
            done: false,
            description: String::new(),
            subtasks: Vec::new(),
            attrs: TaskAttributes::default(),
            file_path: PathBuf::new(),
            line_number: 0,
        }
    }
}

impl Task {
    /// Check if task should be displayed based on date filters
    pub fn is_displayed(&self, today: NaiveDate, lookahead_days: i64) -> bool {
        if self.done {
            return false;
        }
        
        let task_visible = self.attrs.date_attr.is_visible(today, lookahead_days);
        let subtasks_visible = self.subtasks.iter()
            .any(|t| t.is_displayed(today, lookahead_days));
        
        task_visible || subtasks_visible
    }

    /// Generate summary for task list display
    pub fn summary(&self, today: NaiveDate) -> String {
        self.attrs.date_attr.summary(today)
    }

    /// Generate detailed view for a specific task (returns raw markdown for rendering)
    pub fn details(&self, today: NaiveDate) -> String {
        let mut result = String::new();
        // Note: The title will be rendered by the markdown renderer
        result.push_str(&format!("**Title**: {} \n", self.title));
        
        // Date details contain their own markdown formatting
        result.push_str(&self.attrs.date_attr.details(today));
        
        if !self.description.is_empty() {
            result.push_str("**Description**:  \n\n");
            result.push_str(&self.description);
        }
        
        result
    }
}

/// Task sorting key
#[derive(Debug, Clone, PartialEq, Eq, PartialOrd, Ord)]
pub struct TaskSortKey {
    pub priority: i32,
    pub path: Vec<String>,
    pub reminder_delta: Duration,
    pub due_delta: Duration,
}

impl Task {
    /// Generate sorting key for task
    pub fn sort_key(&self, today: NaiveDate) -> TaskSortKey {
        let priority = self.attrs.priority_attr
            .as_ref()
            .map(|p| p.priority)
            .unwrap_or(100000); // Very large number for unprioritized tasks
        
        let reminder_delta = self.attrs.date_attr.reminder_date
            .map(|d| d.signed_duration_since(today))
            .unwrap_or(Duration::zero());
        
        let due_delta = self.attrs.date_attr.due_date
            .map(|d| d.signed_duration_since(today))
            .unwrap_or(Duration::zero());
        
        TaskSortKey {
            priority,
            path: self.path.clone(),
            reminder_delta,
            due_delta,
        }
    }
}

/// Format a date relative to today
pub fn date_relative_to_today(date: NaiveDate, today: NaiveDate, prefix: &str) -> String {
    if date < today {
        let delta = today.signed_duration_since(date);
        format!("**{}{} ago**", prefix, format_days(delta))
    } else if date == today {
        format!("**{}today**", prefix)
    } else {
        let delta = date.signed_duration_since(today);
        format!("{}in {}", prefix, format_days(delta))
    }
}

/// Format duration in days
pub fn format_days(duration: Duration) -> String {
    let days = duration.num_days();
    if days == 1 {
        format!("{} day", days)
    } else {
        format!("{} days", days)
    }
}
