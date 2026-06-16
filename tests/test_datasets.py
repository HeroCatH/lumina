from pathlib import Path

import pytest

from lumina.datasets import Dataset, register_adapter
from lumina.datasets.adapters.base import DatasetAdapter
from lumina.datasets.adapters.csv import CSVAdapter
from lumina.datasets.registry import detect_adapter, get_adapter
from lumina.core.project import Project


CSV_CONTENT = "a,b,c\n1,2,3\n4,5,6\n"


def _write_csv(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(CSV_CONTENT)


def test_dataset_preview(tmp_path):
    csv_path = tmp_path / "data.csv"
    _write_csv(csv_path)
    dataset = Dataset(name="ds", path=csv_path, adapter_type="csv")
    preview = dataset.preview(n=2)
    assert len(preview) == 2
    assert preview[0] == {"a": 1, "b": 2, "c": 3}


def test_dataset_schema(tmp_path):
    csv_path = tmp_path / "data.csv"
    _write_csv(csv_path)
    dataset = Dataset(name="ds", path=csv_path, adapter_type="csv")
    schema = dataset.schema()
    assert schema == {"a": "Int64", "b": "Int64", "c": "Int64"}


def test_dataset_statistics(tmp_path):
    csv_path = tmp_path / "data.csv"
    _write_csv(csv_path)
    dataset = Dataset(name="ds", path=csv_path, adapter_type="csv")
    stats = dataset.statistics()
    assert stats["row_count"] == 2
    assert stats["column_count"] == 3
    assert set(stats["columns"]) == {"a", "b", "c"}
    assert len(stats["numeric_summary"]) > 0


def test_dataset_row_count(tmp_path):
    csv_path = tmp_path / "data.csv"
    _write_csv(csv_path)
    dataset = Dataset(name="ds", path=csv_path, adapter_type="csv")
    assert dataset.row_count() == 2


def test_dataset_from_path_detects_adapter(tmp_path):
    csv_path = tmp_path / "data.csv"
    _write_csv(csv_path)
    dataset = Dataset.from_path(name="ds", path=str(csv_path))
    assert dataset.adapter_type == "csv"
    assert dataset.row_count() == 2


def test_get_adapter_returns_instance():
    adapter = get_adapter("csv")
    assert isinstance(adapter, CSVAdapter)


def test_detect_adapter_csv():
    assert detect_adapter(Path("foo.csv")) == "csv"


def test_register_adapter():
    class FakeAdapter(DatasetAdapter):
        name = "fake"
        supported_extensions = [".fake"]

        def load(self, path):
            return None

        def preview(self, data, n=10):
            return []

        def schema(self, data):
            return {}

        def statistics(self, data):
            return {}

        def row_count(self, data):
            return 0

    register_adapter(FakeAdapter)
    assert isinstance(get_adapter("fake"), FakeAdapter)
    assert detect_adapter(Path("foo.fake")) == "fake"


def test_get_adapter_unknown_raises():
    with pytest.raises(ValueError, match="Unknown dataset adapter"):
        get_adapter("not_real")


def test_detect_adapter_unsupported_extension_raises():
    with pytest.raises(ValueError, match="Cannot detect adapter"):
        detect_adapter(Path("data.txt"))


def test_project_register_dataset_preserves_subdirectory(tmp_path):
    project_path = tmp_path / "proj"
    project_path.mkdir()
    project = Project(project_id="p1", name="proj", path=project_path)
    csv_path = project_path / "datasets" / "subdir" / "data.csv"
    _write_csv(csv_path)

    dataset = project.register_dataset(name="subds", path="subdir/data.csv")

    expected_target = project_path / "datasets" / "subdir" / "data.csv"
    assert dataset.path == expected_target
    assert dataset.row_count() == 2
    record = project.datasets.get_by_name("p1", "subds")
    assert record is not None
    assert record["path"] == str(expected_target)
    assert record["adapter_type"] == "csv"


def test_project_register_dataset_copies_external_absolute_path(tmp_path):
    project_path = tmp_path / "proj"
    project_path.mkdir()
    project = Project(project_id="p2", name="proj", path=project_path)
    external_csv = tmp_path / "external" / "data.csv"
    _write_csv(external_csv)

    dataset = project.register_dataset(name="extds", path=str(external_csv))

    expected_target = project_path / "datasets" / "data.csv"
    assert dataset.path == expected_target
    assert expected_target.exists()
    record = project.datasets.get_by_name("p2", "extds")
    assert record is not None
    assert record["path"] == str(expected_target)
