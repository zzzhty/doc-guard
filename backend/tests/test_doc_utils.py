from app.core.doc_utils import (
    apply_patch_to_section,
    extract_frontmatter,
    extract_sections,
    find_section_by_heading,
    generate_unified_diff,
)


def test_extract_sections_records_heading_metadata_and_ranges():
    sections = extract_sections("# Title\nIntro\n\n## API\nDetails\n\n## Deploy\nSteps")

    assert [section["title"] for section in sections] == ["Title", "API", "Deploy"]
    assert sections[0]["level"] == 1
    assert sections[1]["content"] == "Details\n"


def test_find_section_by_heading_matches_case_insensitively():
    section = find_section_by_heading("# Title\n\n## API Reference\nBody", "api")

    assert section is not None
    assert section["title"] == "API Reference"


def test_apply_patch_to_section_replaces_only_target_section():
    original = "# Guide\nIntro\n\n## Auth\nOld auth docs\n\n## Deploy\nDeploy docs"

    patched = apply_patch_to_section(original, "Auth", "New auth docs")

    assert "## Auth\nNew auth docs" in patched
    assert "Old auth docs" not in patched
    assert "## Deploy\nDeploy docs" in patched


def test_apply_patch_to_section_returns_original_when_heading_missing():
    original = "# Guide\nIntro"

    assert apply_patch_to_section(original, "Missing", "New") == original


def test_generate_unified_diff_uses_document_filename():
    diff = generate_unified_diff("old\n", "new\n", filename="docs/api.md")

    assert "--- a/docs/api.md" in diff
    assert "+++ b/docs/api.md" in diff
    assert "-old" in diff
    assert "+new" in diff


def test_extract_frontmatter_returns_metadata_and_body():
    metadata, body = extract_frontmatter("---\ntitle: API\n---\n# Body")

    assert metadata == {"title": "API"}
    assert body == "\n# Body"
