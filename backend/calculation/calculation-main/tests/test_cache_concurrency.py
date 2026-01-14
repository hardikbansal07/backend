import asyncio
import json
import pathlib
import sys
from httpx import AsyncClient

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / 'src'))

from api.app import app
from api import service


def test_concurrent_requests_and_persistence(tmp_path, monkeypatch):
    # Isolate persistence to a temp location so tests do not mutate real artifacts
    persist_path = tmp_path / "horo_requests.json"
    monkeypatch.setattr(service, "PERSIST_PATH", persist_path)
    service._store.clear()
    service._persisted_requests.clear()

    async def _run():
        payload = {
            "birthDateTime": "1990-01-01T12:00:00",
            "location": {"place": "Chennai,IN", "latitude": 13.0827, "longitude": 80.2707, "tzOffset": 5.5},
            "ayanamsaMode": "TRUE_CITRA",
        }
        async with AsyncClient(app=app, base_url="http://test") as client:
            responses = await asyncio.gather(
                *[client.post('/api/horoscope', json=payload) for _ in range(3)]
            )
            for resp in responses:
                assert resp.status_code == 200, resp.text
            ids = {resp.json()['meta']['requestId'] for resp in responses}
            # Cache/store should deduplicate concurrent requests
            assert len(ids) == 1
            rid = ids.pop()

            render_calls = await asyncio.gather(
                *[client.get(f'/api/horoscope/{rid}/render') for _ in range(6)]
            )
            assert all(rc.status_code in (200, 304) for rc in render_calls)
            etags = [rc.headers.get('etag') for rc in render_calls if rc.status_code == 200]
            assert etags and len(set(etags)) == 1

            async def _writer(idx: int):
                service.upsert_persisted_request(f"req-{idx}", {"idx": idx})
                await service.persist_requests()

            await asyncio.gather(*[_writer(i) for i in range(5)])
            # Final flush to capture all entries after concurrent writes
            await service.persist_requests()

    asyncio.run(_run())
    saved = json.loads(persist_path.read_text())
    assert all(f"req-{i}" in saved for i in range(5))
