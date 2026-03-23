"""Tests for the Jinja2 prompt loader."""

from postwriter.prompts.loader import PromptLoader


def test_has_template():
    loader = PromptLoader()
    assert loader.has_template("architect_premise.j2")
    assert not loader.has_template("nonexistent.j2")


def test_list_templates():
    loader = PromptLoader()
    templates = loader.list_templates()
    assert "architect_premise.j2" in templates


def test_render_template():
    loader = PromptLoader()
    result = loader.render(
        "architect_premise.j2",
        genre="literary thriller",
        setting="Small coastal town, Pacific Northwest",
        time_period="Present day",
        tone="Atmospheric, tense, with moments of dark humor",
        protagonist="A retired forensic linguist returning to her hometown",
        central_conflict="The disappearance of her estranged sister coinciding with threatening letters",
        ending_direction="Ambiguous resolution that redefines the central mystery",
        themes=["the unreliability of language", "family as both refuge and trap"],
        constraints=["No supernatural elements", "Single POV"],
    )

    assert "literary thriller" in result
    assert "forensic linguist" in result
    assert "unreliability of language" in result
    assert "No supernatural elements" in result


def test_render_template_without_optional():
    loader = PromptLoader()
    result = loader.render(
        "architect_premise.j2",
        genre="science fiction",
        setting="Space station",
        time_period="2300",
        tone="Philosophical",
        protagonist="An AI researcher",
        central_conflict="AI sentience debate",
        ending_direction="Open-ended",
        themes=[],
        constraints=[],
    )

    assert "science fiction" in result
    # Should not contain the themes section header since list is empty
    assert "AI researcher" in result
