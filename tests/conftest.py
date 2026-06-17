import pytest


@pytest.fixture(autouse=True)
def _isolated_lumina_root(monkeypatch, tmp_path):
    """Ensure every test writes Lumina projects/state under its own tmp_path."""
    monkeypatch.setenv("LUMINA_PROJECTS_ROOT", str(tmp_path))
