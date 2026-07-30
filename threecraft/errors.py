"""Public-safe domain errors."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class ThreeCraftError(Exception):
    code: str
    message: str
    status_code: int = 400
    retryable: bool = False
    remedies: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        Exception.__init__(self, self.message)

    def to_dict(self, request_id: str | None = None) -> dict[str, object]:
        payload: dict[str, object] = {
            "code": self.code,
            "message": self.message,
            "retryable": self.retryable,
            "remedies": list(self.remedies),
        }
        if request_id:
            payload["requestId"] = request_id
        return payload
