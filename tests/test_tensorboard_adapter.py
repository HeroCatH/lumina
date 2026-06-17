import pytest
from pathlib import Path


def test_tensorboard_adapter_supports_tfevents():
    from lumina.experiments.log_adapters import TensorBoardLogAdapter

    adapter = TensorBoardLogAdapter()
    assert adapter.supports(Path("events.out.tfevents.123"))
    assert not adapter.supports(Path("metrics.jsonl"))


def test_tensorboard_adapter_requires_tensorboard():
    from lumina.experiments.log_adapters import TensorBoardLogAdapter

    adapter = TensorBoardLogAdapter()
    if adapter._available:
        pytest.skip("tensorboard is installed; skipping absence test")
    with pytest.raises(RuntimeError, match="tensorboard is not installed"):
        list(adapter.parse(Path("events.out.tfevents.123")))
