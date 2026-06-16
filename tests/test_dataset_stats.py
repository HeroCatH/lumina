from pathlib import Path
from lumina.datasets.dataset import Dataset


def test_dataset_statistics(tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("a,b,c\n1,2,x\n4,5,y\n7,8,z\n")
    dataset = Dataset.from_path("test", str(csv_path))
    stats = dataset.statistics()
    assert stats["row_count"] == 3
    assert stats["column_count"] == 3
    assert "a" in stats["columns"]
    assert "column_types" in stats
    assert "missing_counts" in stats
    assert stats["column_types"]["a"].startswith("Int")
