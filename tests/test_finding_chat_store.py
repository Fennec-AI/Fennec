"""Finding chat is durable across store instances and isolated by finding."""

import pytest

from src.api.finding_chat_store import FindingChatStore


@pytest.mark.asyncio
async def test_history_survives_reopening_database(tmp_path):
    db_path = tmp_path / "nested" / "chat.sqlite3"
    store = FindingChatStore(db_path)
    assert await store.list_messages("finding-a") == []
    await store.append_exchange("finding-a", "Explain it", "Observed SQL injection")
    await store.append_exchange("finding-b", "Other question", "Other answer")

    reopened = FindingChatStore(db_path)
    assert await reopened.list_messages("finding-a") == [
        {"role": "user", "content": "Explain it"},
        {"role": "assistant", "content": "Observed SQL injection"},
    ]
    assert await reopened.recent_messages("finding-a", limit=1) == [
        {"role": "assistant", "content": "Observed SQL injection"},
    ]
    await reopened.clear("finding-a")
    assert await store.list_messages("finding-a") == []
    imported = [{"role": "user", "content": "Saved in browser"}]
    assert await reopened.import_if_empty("finding-a", imported) == imported
    assert await store.import_if_empty("finding-a", imported) == imported
    assert len(await store.list_messages("finding-b")) == 2
