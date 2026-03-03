from __future__ import annotations

import pytest

from bot.db.database import Database


@pytest.fixture
async def db():
    database = Database(":memory:")
    await database.connect()
    await database.init_schema()
    yield database
    await database.close()
