from lovdata_chat.answer_style import get_style_guide


def test_explanation_levels_have_distinct_guides() -> None:
    easy = get_style_guide("lett")
    professor = get_style_guide("professor")
    assert easy["level"] == "lett"
    assert professor["level"] == "professor"
    assert "Kort forklart" in easy["required_sections"]
    assert "Rettskildebildet" in professor["required_sections"]
    assert easy["instructions"] != professor["instructions"]
