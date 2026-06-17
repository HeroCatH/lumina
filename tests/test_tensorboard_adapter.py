import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from lumina.experiments.log_adapters import LogParseError, TensorBoardLogAdapter


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


def test_tensorboard_adapter_parse_with_mock():
    adapter = TensorBoardLogAdapter()
    if not adapter._available:
        pytest.skip("tensorboard is not installed; skipping parse test")
    mock_acc = MagicMock()
    mock_acc.Tags.return_value = {"scalars": ["loss"]}
    mock_event = MagicMock(step=1, value=0.5)
    mock_acc.Scalars.return_value = [mock_event]

    with patch.object(adapter, "_EventAccumulator", return_value=mock_acc):
        records = list(adapter.parse(Path("events.out.tfevents.123")))

    assert len(records) == 1
    assert records[0] == {"step": 1, "name": "loss", "value": 0.5}


def test_tensorboard_adapter_parse_error():
    adapter = TensorBoardLogAdapter()
    if not adapter._available:
        pytest.skip("tensorboard is not installed; skipping parse error test")
    mock_acc = MagicMock()
    mock_acc.Tags.side_effect = RuntimeError("bad file")

    with patch.object(adapter, "_EventAccumulator", return_value=mock_acc):
        with pytest.raises(LogParseError):
            list(adapter.parse(Path("events.out.tfevents.123")))
