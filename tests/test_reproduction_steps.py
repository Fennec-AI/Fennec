"""A finding retains its proof when missing reproduction instructions are recovered."""

from types import SimpleNamespace

import pytest

from src.agents import pentester
from src.schemas.pentester_result import (
    FindingEvidence,
    LoggedEvidence,
    PentesterResult,
    has_missing_rich_fields,
)


@pytest.mark.asyncio
async def test_gap_filler_adds_steps_without_replacing_evidence(monkeypatch):
    original = FindingEvidence(
        logged_evidence=[LoggedEvidence(request="POST /login", response="HTTP 200")],
        payloads_used=["example-payload"],
        observed_behavior="The response exposed rows",
        reproduction_steps=[],
    )
    partial = PentesterResult(status="completed", verdict="high", evidence_details=original)
    assert "evidence_details" in has_missing_rich_fields(partial)

    class FakeExtractor:
        async def ainvoke(self, messages):
            assert "reproduction_steps=missing" in messages[-1].content
            return {"parsed": SimpleNamespace(evidence_details={
                "reproduction_steps": [
                    "Acesse /login e prepare a requisição POST registrada.",
                    "Envie o payload registrado e confira a resposta HTTP 200.",
                ],
            })}

    monkeypatch.setattr(pentester, "structured_llm", lambda *_args, **_kwargs: FakeExtractor())
    filled = await pentester._fill_missing_rich_fields(
        object(), [], partial, ["evidence_details"]
    )
    assert filled.evidence_details.reproduction_steps[0].startswith("Acesse")
    assert filled.evidence_details.logged_evidence == original.logged_evidence
    assert filled.evidence_details.payloads_used == original.payloads_used
    assert filled.evidence_details.observed_behavior == original.observed_behavior
