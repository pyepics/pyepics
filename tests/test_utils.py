from unittest import mock

import pytest

from epics.utils import bytes2str


@pytest.mark.parametrize(
    "input_bytes, expected_str, raises_exc",
    [
        (b"hello", "hello", False),
        ("hello", "hello", False),
        ("°".encode("latin1"), "°", True),
        ("°".encode("utf-8"), "°", False),
        (1, 1, False),
    ],
)
def test_bytes2str_without_charset_normalizer(input_bytes, expected_str, raises_exc):
    with mock.patch("epics.utils.from_bytes", None):
        if raises_exc:
            with pytest.raises(UnicodeDecodeError):
                bytes2str(input_bytes)
        else:
            assert bytes2str(input_bytes) == expected_str


@pytest.mark.parametrize(
    "input_bytes, expected_str, raises_exc",
    [
        (b"hello", "hello", False),
        ("hello", "hello", False),
        ("°".encode("latin1"), "ﺍ", False),  # latin1 decoding doesn't work but it doesn't raise
        ("°".encode("utf-8"), "°", False),
        (1, "1", False),
    ],
)
def test_bytes2str_with_charset_normalizer(input_bytes, expected_str, raises_exc):
    if raises_exc:
        with pytest.raises(UnicodeDecodeError):
            bytes2str(input_bytes)
    else:
        assert bytes2str(input_bytes) == expected_str
