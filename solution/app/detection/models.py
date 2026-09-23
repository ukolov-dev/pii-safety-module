"""Domain models for deterministic PII detection."""

from dataclasses import dataclass, field


@dataclass(frozen=True, slots=True)
class DetectedEntity:
    """A half-open span of personally identifiable information in source text."""

    entity_type: str
    start: int
    end: int
    text: str
    confidence: float
    source: str
    priority: int = field(default=0, repr=False, compare=False)

    def __post_init__(self) -> None:
        if self.start < 0 or self.end <= self.start:
            raise ValueError("entity offsets must form a non-empty half-open span")
        if len(self.text) != self.end - self.start:
            raise ValueError("entity text must match its offsets")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0 and 1")

