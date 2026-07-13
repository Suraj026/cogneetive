import aiosqlite
from typing import List


class SourceRegistry:
    """SQLite-backed entity-to-source mapping for graph node attribution."""

    def __init__(self, db_path: str = "source_registry.db"):
        self.db_path = db_path

    async def _ensure_table(self, conn: aiosqlite.Connection):
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS entity_sources (
                entity_name TEXT NOT NULL,
                source TEXT NOT NULL,
                ingested_at TEXT NOT NULL DEFAULT (datetime('now')),
                PRIMARY KEY (entity_name, source)
            )
        """)
        await conn.commit()

    async def _get_conn(self) -> aiosqlite.Connection:
        conn = await aiosqlite.connect(self.db_path)
        await self._ensure_table(conn)
        return conn

    async def tag(self, entity_name: str, source: str) -> None:
        """Record that an entity belongs to a source."""
        conn = await self._get_conn()
        try:
            await conn.execute(
                "INSERT OR IGNORE INTO entity_sources (entity_name, source) VALUES (?, ?)",
                (entity_name, source),
            )
            await conn.commit()
        finally:
            await conn.close()

    async def get_sources(self, entity_name: str) -> List[str]:
        """Get all sources for an entity."""
        conn = await self._get_conn()
        try:
            cursor = await conn.execute(
                "SELECT source FROM entity_sources WHERE entity_name = ?",
                (entity_name,),
            )
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
        finally:
            await conn.close()

    async def get_entities_by_source(self, source: str) -> List[str]:
        """Get all entity names tagged with a given source."""
        conn = await self._get_conn()
        try:
            cursor = await conn.execute(
                "SELECT entity_name FROM entity_sources WHERE source = ?",
                (source,),
            )
            rows = await cursor.fetchall()
            return [row[0] for row in rows]
        finally:
            await conn.close()

    async def remove_source(self, source: str) -> None:
        """Remove all entity mappings for a source."""
        conn = await self._get_conn()
        try:
            await conn.execute(
                "DELETE FROM entity_sources WHERE source = ?",
                (source,),
            )
            await conn.commit()
        finally:
            await conn.close()

    async def get_all(self) -> dict[str, list[str]]:
        """Get all entity→sources mappings."""
        conn = await self._get_conn()
        try:
            cursor = await conn.execute(
                "SELECT entity_name, source FROM entity_sources ORDER BY entity_name"
            )
            rows = await cursor.fetchall()
            result: dict[str, list[str]] = {}
            for entity, source in rows:
                result.setdefault(entity, []).append(source)
            return result
        finally:
            await conn.close()

    async def get_source_counts(self) -> dict[str, int]:
        """Get count of distinct entities per source."""
        conn = await self._get_conn()
        try:
            cursor = await conn.execute(
                "SELECT source, COUNT(DISTINCT entity_name) FROM entity_sources GROUP BY source"
            )
            rows = await cursor.fetchall()
            return {row[0]: row[1] for row in rows}
        finally:
            await conn.close()

    async def close(self) -> None:
        """No-op for aiosqlite (connections are closed per-op). Kept for API consistency."""
        pass
