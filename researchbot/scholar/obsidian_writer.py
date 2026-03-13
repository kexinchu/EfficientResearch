"""Write structured notes to Obsidian vault as markdown with YAML frontmatter."""
from pathlib import Path
from typing import Optional

from researchbot.config import get_obsidian_vault_path
from researchbot.models import PaperNote, IdeaNote
from researchbot.tools.io import write_markdown


def _sanitize_filename(name: str) -> str:
    """Sanitize a string for use as a filename."""
    # Remove or replace characters invalid in filenames
    invalid = '<>:"/\\|?*'
    for ch in invalid:
        name = name.replace(ch, "")
    # Collapse whitespace
    name = " ".join(name.split())
    # Truncate
    return name[:120].strip()


def _format_yaml_list(items: list) -> str:
    """Format a list for YAML frontmatter."""
    if not items:
        return "[]"
    lines = "\n".join(f"  - {item}" for item in items)
    return f"\n{lines}"


def _format_section(content) -> str:
    """Format a note section, handling both strings and lists."""
    if isinstance(content, list):
        return "\n".join(f"- {item}" for item in content)
    return str(content) if content else ""


def write_paper_note(
    note: PaperNote,
    vault_path: Optional[str] = None,
) -> Path:
    """Write a paper note to Obsidian vault under 论文/<paper_type>/.

    Returns the path to the written file.
    """
    vault = Path(vault_path or get_obsidian_vault_path())
    paper_dir = vault / "论文" / note.paper_type
    filename = _sanitize_filename(note.title) + ".md"
    filepath = paper_dir / filename

    authors_yaml = _format_yaml_list(note.authors)
    tags_yaml = _format_yaml_list(note.tags)

    md = f"""---
title: "{note.title}"
type: paper
paper_type: {note.paper_type}
authors: {authors_yaml}
year: {note.year or ""}
venue: "{note.venue}"
source_url: "{note.source_url}"
zotero_key: "{note.zotero_key}"
tags: {tags_yaml}
created_at: {note.created_at}
updated_at: {note.updated_at}
status: {note.status}
---

# {note.title}

## Problem
{_format_section(note.problem)}

## Importance
{_format_section(note.importance)}

## Method

### Motivation
{_format_section(note.motivation)}

### Challenge
{_format_section(note.challenge)}

### Design
{_format_section(note.design)}

## Key Results
{_format_section(note.key_results)}

## Summary
{_format_section(note.summary)}

## Limitations
{_format_section(note.limitations)}

## Insights for My Research
{_format_section(note.insights)}

## Personal Notes
{_format_section(note.personal_notes)}
"""

    write_markdown(filepath, md)
    return filepath


def write_idea_note(
    note: IdeaNote,
    vault_path: Optional[str] = None,
) -> Path:
    """Write an idea note to Obsidian vault under Idea/.

    Returns the path to the written file.
    """
    vault = Path(vault_path or get_obsidian_vault_path())
    idea_dir = vault / "Idea"
    filename = _sanitize_filename(note.title) + ".md"
    filepath = idea_dir / filename

    tags_yaml = _format_yaml_list(note.tags)

    md = f"""---
title: "{note.title}"
type: idea
tags: {tags_yaml}
created_at: {note.created_at}
updated_at: {note.updated_at}
status: {note.status}
---

# {note.title}

## Hypothesis
{_format_section(note.hypothesis)}

## Motivation
{_format_section(note.motivation)}

## Related Directions
{_format_section(note.related_directions)}

## Open Questions
{_format_section(note.open_questions)}

## Next Steps
{_format_section(note.next_steps)}

## Personal Notes
{_format_section(note.personal_notes)}
"""

    write_markdown(filepath, md)
    return filepath
