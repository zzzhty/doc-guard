import difflib
import re


def extract_sections(markdown_content: str) -> list[dict]:
    """Extract sections from markdown content by heading level."""
    sections = []
    lines = markdown_content.split("\n")
    current_section = None

    for i, line in enumerate(lines):
        heading_match = re.match(r"^(#{1,4})\s+(.+)", line)
        if heading_match:
            if current_section:
                current_section["line_end"] = i - 1
                sections.append(current_section)
            current_section = {
                "heading": line,
                "level": len(heading_match.group(1)),
                "title": heading_match.group(2).strip(),
                "content": "",
                "line_start": i,
                "line_end": i,
            }
        elif current_section:
            if current_section["content"]:
                current_section["content"] += "\n"
            current_section["content"] += line

    if current_section:
        current_section["line_end"] = len(lines) - 1
        sections.append(current_section)

    return sections


def find_section_by_heading(content: str, heading_text: str) -> dict | None:
    sections = extract_sections(content)
    for s in sections:
        if heading_text.lower() in s["title"].lower():
            return s
    return None


def generate_unified_diff(original: str, patched: str, filename: str = "document.md") -> str:
    """Generate a unified diff string."""
    return "".join(
        difflib.unified_diff(
            original.splitlines(keepends=True),
            patched.splitlines(keepends=True),
            fromfile=f"a/{filename}",
            tofile=f"b/{filename}",
        )
    )


def apply_patch_to_section(original_content: str, heading: str, new_section_content: str) -> str:
    """Replace a section identified by heading with new content."""
    sections = extract_sections(original_content)
    target = None
    for s in sections:
        if heading.lower() in s["title"].lower():
            target = s
            break

    if not target:
        return original_content

    lines = original_content.split("\n")
    before = lines[: target["line_start"]]
    after = lines[target["line_end"] + 1 :]

    result = before
    result.append(target["heading"])
    result.extend(new_section_content.split("\n"))
    result.extend(after)
    return "\n".join(result)


def extract_frontmatter(content: str) -> tuple[dict, str]:
    """Extract YAML frontmatter from markdown content. Returns (metadata, body)."""
    if content.startswith("---"):
        parts = content.split("---", 2)
        if len(parts) >= 3:
            import yaml
            try:
                meta = yaml.safe_load(parts[1]) or {}
            except yaml.YAMLError:
                meta = {}
            return meta, parts[2]
    return {}, content
