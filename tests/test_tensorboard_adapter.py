import pytest
from pathlib import Path

from lumina.experiments.log_adapters import TensorBoardLogAdapter


def test_tensorboard_adapter_supports_tfevents():
    adapter = TensorBoardLogAdapter()
    if adapter._available:
        assert adapter.supports(Path("events.out.tfevents.123"))
    assert not adapter.supports(Path("metrics.jsonl"))


def test_tensorboard_adapter_skips_when_unavailable():
    adapter = TensorBoardLogAdapter()
    if adapter._available:
        pytest.skip("tensorboard is installed; skipping absence test")
    assert not adapter.supports(Path("events.out.tfevents.123"))
