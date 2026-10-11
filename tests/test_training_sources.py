import io
import zipfile

import pytest

from scripts.prepare_training_sources import RangeReader


def test_range_reader_extracts_only_small_member():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("train/train_tables.json", b'[{"db_id":"toy"}]')
        archive.writestr("train/large.sqlite", b"x" * 100000)
    source = buffer.getvalue()
    fetched = []

    def fetch(start, end):
        fetched.append((start, end))
        return source[start : end + 1]

    with zipfile.ZipFile(RangeReader(len(source), fetch)) as archive:
        assert archive.read("train/train_tables.json") == b'[{"db_id":"toy"}]'
    assert sum(end - start + 1 for start, end in fetched) < 1000


def test_range_reader_refuses_full_archive_read():
    reader = RangeReader(10000000, lambda start, end: b"")
    with pytest.raises(ValueError, match="range cap"):
        reader.read()


def test_short_range_response_is_refused():
    reader = RangeReader(100, lambda start, end: b"x")
    with pytest.raises(ValueError, match="short range"):
        reader.read(10)


def test_total_network_budget_is_enforced():
    reader = RangeReader(200, lambda start, end: b"x" * (end - start + 1), budget=10)
    assert reader.read(6) == b"xxxxxx"
    with pytest.raises(ValueError, match="network budget"):
        reader.read(5)
