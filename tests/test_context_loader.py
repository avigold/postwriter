"""Tests for the context file loader."""

import tempfile
from pathlib import Path

from postwriter.context.loader import ContextLoader, ContextType


def _make_context_dir() -> Path:
    td = Path(tempfile.mkdtemp())
    ctx = td / "context"
    ctx.mkdir()
    return ctx


def test_load_empty_dir():
    ctx = _make_context_dir()
    loader = ContextLoader(ctx)
    files = loader.load()
    assert files == []
    assert loader.summary() == "No context files found."


def test_load_nonexistent_dir():
    loader = ContextLoader(Path("/nonexistent/dir"))
    files = loader.load()
    assert files == []


def test_load_markdown_with_frontmatter():
    ctx = _make_context_dir()
    (ctx / "guide.md").write_text("---\ntype: guidelines\n---\nWrite clearly.")

    loader = ContextLoader(ctx)
    files = loader.load()
    assert len(files) == 1
    assert files[0].context_type == ContextType.GUIDELINES
    assert files[0].content == "Write clearly."
    assert files[0].frontmatter["type"] == "guidelines"


def test_load_markdown_infer_from_filename():
    ctx = _make_context_dir()
    (ctx / "character-notes.md").write_text("Elena is a retired professor.")

    loader = ContextLoader(ctx)
    files = loader.load()
    assert len(files) == 1
    assert files[0].context_type == ContextType.CHARACTERS


def test_load_multiple_types():
    ctx = _make_context_dir()
    (ctx / "style-guide.md").write_text("Sparse prose. Short sentences.")
    (ctx / "plot-outline.md").write_text("Three acts.")
    (ctx / "world-notes.md").write_text("Coastal Maine, 1987.")
    (ctx / "sample-writing.md").write_text("The door opened slowly.")

    loader = ContextLoader(ctx)
    files = loader.load()
    assert len(files) == 4

    types = {f.context_type for f in files}
    assert ContextType.STYLE in types
    assert ContextType.PLOT in types
    assert ContextType.WORLD in types
    assert ContextType.SAMPLE_WRITING in types


def test_load_image_file():
    ctx = _make_context_dir()
    (ctx / "mood-board.png").write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)

    loader = ContextLoader(ctx)
    files = loader.load()
    assert len(files) == 1
    assert files[0].is_image is True
    assert files[0].context_type == ContextType.IMAGE


def test_refresh_detects_new_files():
    ctx = _make_context_dir()
    (ctx / "plot.md").write_text("Initial plot.")

    loader = ContextLoader(ctx)
    loader.load()
    assert len(loader.files) == 1

    (ctx / "characters.md").write_text("New character file.")
    new = loader.refresh()
    assert len(new) == 1
    assert new[0].context_type == ContextType.CHARACTERS
    assert len(loader.files) == 2


def test_refresh_detects_changed_files():
    ctx = _make_context_dir()
    f = ctx / "plot.md"
    f.write_text("Version 1")

    loader = ContextLoader(ctx)
    loader.load()

    f.write_text("Version 2")
    changed = loader.refresh()
    assert len(changed) == 1
    assert "Version 2" in changed[0].content


def test_refresh_detects_deleted_files():
    ctx = _make_context_dir()
    f = ctx / "plot.md"
    f.write_text("Will be deleted")
    (ctx / "keep.md").write_text("Stays")

    loader = ContextLoader(ctx)
    loader.load()
    assert len(loader.files) == 2

    f.unlink()
    loader.refresh()
    assert len(loader.files) == 1


def test_get_by_type():
    ctx = _make_context_dir()
    (ctx / "style1.md").write_text("---\ntype: style\n---\nBe concise.")
    (ctx / "style2.md").write_text("---\ntype: style\n---\nAvoid adverbs.")
    (ctx / "plot.md").write_text("---\ntype: plot\n---\nThree acts.")

    loader = ContextLoader(ctx)
    loader.load()

    style_files = loader.get_by_type(ContextType.STYLE)
    assert len(style_files) == 2

    plot_files = loader.get_by_type(ContextType.PLOT)
    assert len(plot_files) == 1


def test_get_text_content():
    ctx = _make_context_dir()
    (ctx / "style.md").write_text("---\ntype: style\n---\nBe concise.")
    (ctx / "plot.md").write_text("---\ntype: plot\n---\nThree acts.")

    loader = ContextLoader(ctx)
    loader.load()

    all_text = loader.get_text_content()
    assert "Be concise" in all_text
    assert "Three acts" in all_text

    style_only = loader.get_text_content(ContextType.STYLE)
    assert "Be concise" in style_only
    assert "Three acts" not in style_only


def test_manifest():
    ctx = _make_context_dir()
    (ctx / "plot.md").write_text("Act 1. Act 2. Act 3.")

    loader = ContextLoader(ctx)
    loader.load()

    manifest = loader.manifest.to_dict()
    assert len(manifest) == 1
    assert manifest[0]["type"] == "plot"
    assert "hash" in manifest[0]


def test_skips_hidden_files():
    ctx = _make_context_dir()
    (ctx / ".hidden.md").write_text("Should be skipped")
    (ctx / "visible.md").write_text("Should be loaded")

    loader = ContextLoader(ctx)
    files = loader.load()
    assert len(files) == 1
    assert files[0].name == "visible.md"


def test_skips_unrecognized_extensions():
    ctx = _make_context_dir()
    (ctx / "data.json").write_text("{}")
    (ctx / "notes.md").write_text("Real content")

    loader = ContextLoader(ctx)
    files = loader.load()
    assert len(files) == 1
