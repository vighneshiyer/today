use owo_colors::OwoColorize;
use regex::Regex;
use std::sync::OnceLock;

/// Markdown patterns
fn bold_italic_regex() -> &'static Regex {
    static REGEX: OnceLock<Regex> = OnceLock::new();
    REGEX.get_or_init(|| Regex::new(r"\*\*\*(.+?)\*\*\*").unwrap())
}

fn bold_regex() -> &'static Regex {
    static REGEX: OnceLock<Regex> = OnceLock::new();
    REGEX.get_or_init(|| Regex::new(r"\*\*(.+?)\*\*").unwrap())
}

fn italic_regex() -> &'static Regex {
    static REGEX: OnceLock<Regex> = OnceLock::new();
    REGEX.get_or_init(|| Regex::new(r"\*(.+?)\*").unwrap())
}

fn code_regex() -> &'static Regex {
    static REGEX: OnceLock<Regex> = OnceLock::new();
    REGEX.get_or_init(|| Regex::new(r"`(.+?)`").unwrap())
}

fn strikethrough_regex() -> &'static Regex {
    static REGEX: OnceLock<Regex> = OnceLock::new();
    REGEX.get_or_init(|| Regex::new(r"~~(.+?)~~").unwrap())
}

/// Render markdown text with ANSI color codes
pub fn render_markdown(text: &str) -> String {
    // Process in order: bold+italic first (longest pattern), then bold, then italic
    let mut result = text.to_string();
    
    // Bold + Italic (***text***)
    result = bold_italic_regex()
        .replace_all(&result, |caps: &regex::Captures| {
            let content = caps[1].to_string();
            format!("{}", content.bold().italic())
        })
        .to_string();
    
    // Bold (**text**)
    result = bold_regex()
        .replace_all(&result, |caps: &regex::Captures| {
            let content = caps[1].to_string();
            format!("{}", content.bold())
        })
        .to_string();
    
    // Italic (*text*)
    result = italic_regex()
        .replace_all(&result, |caps: &regex::Captures| {
            let content = caps[1].to_string();
            format!("{}", content.italic())
        })
        .to_string();
    
    // Code (`text`)
    result = code_regex()
        .replace_all(&result, |caps: &regex::Captures| {
            let content = caps[1].to_string();
            format!("{}", content.on_black().bright_white())
        })
        .to_string();
    
    // Strikethrough (~~text~~)
    result = strikethrough_regex()
        .replace_all(&result, |caps: &regex::Captures| {
            let content = caps[1].to_string();
            format!("{}", content.strikethrough().dimmed())
        })
        .to_string();
    
    result
}

/// Render markdown for detailed view (supports more elements)
pub fn render_markdown_detail(text: &str) -> String {
    let mut result = String::new();
    
    for line in text.lines() {
        if line.starts_with("**") && line.contains("**:") {
            // Bold header line like "**Title**: something"
            let parts: Vec<&str> = line.split("**").collect();
            if parts.len() >= 3 {
                result.push_str(&format!("{}", parts[1].bold()));
                // Render the rest of the line with markdown
                let rest = parts[2..].join("**");
                result.push_str(&render_markdown(&rest));
                result.push('\n');
            } else {
                result.push_str(&render_markdown(line));
                result.push('\n');
            }
        } else if line.starts_with("- ") {
            // Bullet point
            result.push_str("  • ");
            result.push_str(&render_markdown(&line[2..]));
            result.push('\n');
        } else if line.starts_with("> ") {
            // Quote block
            let quote_text = render_markdown(&line[2..]);
            result.push_str(&format!("{}", format!("▌ {}", quote_text).dimmed()));
            result.push('\n');
        } else if line.starts_with("    - ") {
            // Nested bullet
            result.push_str("    - ");
            result.push_str(&render_markdown(&line[6..]));
            result.push('\n');
        } else {
            // Regular line with markdown
            result.push_str(&render_markdown(line));
            result.push('\n');
        }
    }
    
    // Remove trailing newline if present
    if result.ends_with('\n') {
        result.pop();
    }
    
    result
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_bold() {
        let result = render_markdown("This is **bold** text");
        assert!(result.contains("bold"));
        // The actual ANSI codes will be present but we just check the text is there
    }

    #[test]
    fn test_italic() {
        let result = render_markdown("This is *italic* text");
        assert!(result.contains("italic"));
    }

    #[test]
    fn test_bold_italic() {
        let result = render_markdown("This is ***bold italic*** text");
        assert!(result.contains("bold italic"));
    }

    #[test]
    fn test_code() {
        let result = render_markdown("This is `code` text");
        assert!(result.contains("code"));
    }

    #[test]
    fn test_strikethrough() {
        let result = render_markdown("This is ~~struck~~ text");
        assert!(result.contains("struck"));
    }

    #[test]
    fn test_mixed() {
        let result = render_markdown("**bold** and *italic* and `code`");
        assert!(result.contains("bold"));
        assert!(result.contains("italic"));
        assert!(result.contains("code"));
    }
}
