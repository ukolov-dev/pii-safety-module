from dataclasses import dataclass

from app.masking import mask_text, unmask_text


@dataclass
class Span:
    entity_type: str
    start: int
    end: int
    text: str


def test_repeated_value_uses_one_token_and_roundtrips() -> None:
    source = "ivan@example.com и снова ivan@example.com"
    entities = [
        Span("EMAIL", 0, 16, "ivan@example.com"),
        Span("EMAIL", 25, 41, "ivan@example.com"),
    ]

    masked = mask_text(source, entities)

    assert masked.text == "{{EMAIL_1}} и снова {{EMAIL_1}}"
    assert unmask_text(masked.text, masked.mapping) == source


def test_unknown_token_is_not_replaced() -> None:
    assert unmask_text("{{PERSON_2}}", {"{{PERSON_1}}": "Иван"}) == "{{PERSON_2}}"

