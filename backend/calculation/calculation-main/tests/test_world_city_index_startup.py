import pytest
from fastapi.testclient import TestClient

from src.api import app as api_app, service


def test_health_reports_world_city_ready():
    service._reset_world_city_index_cache_for_tests()
    with TestClient(api_app.app) as client:
        response = client.get('/api/health')
    payload = response.json()
    assert payload.get('worldCityIndexReady') is True
    assert 'worldCityIndexError' not in payload


def test_startup_fails_when_world_city_file_missing(monkeypatch, tmp_path):
    service._reset_world_city_index_cache_for_tests()
    original_path = service.WORLD_CITY_DATA_PATH
    missing_path = tmp_path / 'world_cities_with_tz.csv'
    monkeypatch.setattr(service, 'WORLD_CITY_DATA_PATH', missing_path)
    with pytest.raises(FileNotFoundError):
        with TestClient(api_app.app):
            pass
    monkeypatch.setattr(service, 'WORLD_CITY_DATA_PATH', original_path)
    service._reset_world_city_index_cache_for_tests()
