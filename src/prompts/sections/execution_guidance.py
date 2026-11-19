"""Load the shared agent rules from the canonical project prompt file."""

from pathlib import Path


AGENT_GUIDANCE_PATH = Path(__file__).resolve().parents[1] / "AGENT.md"


def get_execution_guidance() -> str:
    """Read current rules for every new agent prompt, including file edits."""
    content = AGENT_GUIDANCE_PATH.read_text(encoding="utf-8").strip()
    if not content:
        raise ValueError(f"Agent rules file is empty: {AGENT_GUIDANCE_PATH}")
    return f"<execution_guidance>\n{content}\n</execution_guidance>"
