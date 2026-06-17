from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from lumina.experiments.log_adapters import LogParseError, TensorBoardLogAdapter


def test_tensorboard_adapter_supports_tfevents():
    adapter = TensorBoardLogAdapter()
    with patch.object(adapter, "_available", True):
        assert adapter.supports(Path("events.out.tfevents.123"))
    assert not adapter.supports(Path("metrics.jsonl"))


def test_tensorboard_adapter_skips_when_unavailable():
    adapter = TensorBoardLogAdapter()
    with patch.object(adapter, "_available", False):
        assert not adapter.supports(Path("events.out.tfevents.123"))


def test_tensorboard_adapter_parse_with_mock():
    adapter = TensorBoardLogAdapter()
    mock_acc = MagicMock()
    mock_acc.Tags.return_value = {"scalars": ["loss"]}
    mock_event = MagicMock(step=1, value=0.5)
    mock_acc.Scalars.return_value = [mock_event]

    with patch.object(adapter, "_available", True):
        with patch.object(adapter, "_EventAccumulator", return_value=mock_acc, create=True):
            records = list(adapter.parse(Path("events.out.tfevents.123")))

    assert len(records) == 1
    assert records[0] == {"step": 1, "name": "loss", "value": 0.5}


def test_tensorboard_adapter_parse_error():
    adapter = TensorBoardLogAdapter()
    mock_acc = MagicMock()
    mock_acc.Tags.side_effect = ValueError("bad file")

    with patch.object(adapter, "_available", True):
        with patch.object(adapter, "_EventAccumulator", return_value=mock_acc, create=True):
            with pytest.raises(LogParseError):
                list(adapter.parse(Path("events.out.tfevents.123")))


def test_tensorboard_adapter_parse_when_unavailable():
    adapter = TensorBoardLogAdapter()
    with patch.object(adapter, "_available", False):
        with pytest.raises(LogParseError):
            list(adapter.parse(Path("events.out.tfevents.123")))
