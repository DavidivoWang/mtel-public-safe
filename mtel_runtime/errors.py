from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MTELRuntimeError(Exception):
    code: str
    message: str
    source: str | None = None
    line: int | None = None

    def __str__(self) -> str:
        return self.message

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {"code": self.code, "message": self.message}
        if self.source is not None:
            payload["source"] = self.source
        if self.line is not None:
            payload["line"] = self.line
        return payload
