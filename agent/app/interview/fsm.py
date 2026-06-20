"""Customer-interview state machine.

A short scripted interview the customer answers by voice or chat. Each answer
advances the script; when done, the transcript is summarized into a validated
insight for the brand. Pure + deterministic → unit-testable; the voice channel
(Deepgram) and web `/u/session` drive it.
"""

from __future__ import annotations

from dataclasses import dataclass, field

DEFAULT_QUESTIONS = [
    "What made you pick us over the alternatives?",
    "What's the one thing you'd change about the product or experience?",
    "When did you last almost not buy — and why?",
    "What would make you recommend us to a friend?",
]


@dataclass
class Interview:
    brand: str
    customer: str
    questions: list[str] = field(default_factory=lambda: list(DEFAULT_QUESTIONS))
    idx: int = 0
    transcript: list[dict[str, str]] = field(default_factory=list)
    done: bool = False

    def start(self) -> str:
        """Return the first question (agent turn)."""
        q = self.questions[0]
        self.transcript.append({"role": "agent", "text": q})
        return q

    def answer(self, text: str) -> str | None:
        """Record an answer; return the next question, or None when finished."""
        if self.done:
            return None
        self.transcript.append({"role": "customer", "text": text})
        self.idx += 1
        if self.idx >= len(self.questions):
            self.done = True
            return None
        q = self.questions[self.idx]
        self.transcript.append({"role": "agent", "text": q})
        return q

    def progress(self) -> tuple[int, int]:
        return (self.idx, len(self.questions))

    def customer_answers(self) -> list[str]:
        return [t["text"] for t in self.transcript if t["role"] == "customer"]
