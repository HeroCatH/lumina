from pathlib import Path
from lumina.datasets.adapters.csv import CSVAdapter


def test_csv_adapter(tmp_path):
    csv_path = tmp_path / "data.csv"
    csv_path.write_text("a,b,c\n1,2,3\n4,5,6\n")
    adapter = CSVAdapter()
    df = adapter.load(csv_path)
    preview = adapter.preview(df, n=2)
    assert len(preview) == 2
    assert preview[0] == {"a": "1", "b": "2", "c": "3"}
