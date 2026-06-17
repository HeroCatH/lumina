import lumina
from pathlib import Path

# Create a demo project
project = lumina.create_project("demo_project")

# Create a sample CSV
csv_path = project.path / "datasets" / "sample.csv"
csv_path.parent.mkdir(parents=True, exist_ok=True)
csv_path.write_text("x,y,label\n1,2,A\n3,4,B\n5,6,A\n")

# Register dataset
project.register_dataset("sample", str(csv_path))

# Open UI
lumina.view_project(project, port=8080)
