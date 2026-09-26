"""Tests for data parsers: CSV, JSON, XML ingestion."""
import sys
import os
import tempfile
import json
from pathlib import Path

import pytest
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from ml.pipeline.ingest import ingest, detect_format, load_csv, load_json, load_xml


@pytest.fixture
def sample_csv(tmp_path):
    csv_path = tmp_path / "test.csv"
    csv_path.write_text(
        "timestamp,src_ip,dst_ip,txid,fee\n"
        "2024-09-01T00:00:00Z,192.168.1.1,10.0.0.1,abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234,0.001\n"
        "2024-09-02T00:00:00Z,192.168.1.2,10.0.0.2,ef561234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234abcd1234,0.002\n"
    )
    return csv_path


@pytest.fixture
def sample_json(tmp_path):
    json_path = tmp_path / "test.json"
    data = [
        {"timestamp": "2024-09-01T00:00:00Z", "src_ip": "192.168.1.1", "txid": "abcd" * 16, "fee": 0.001},
        {"timestamp": "2024-09-02T00:00:00Z", "src_ip": "192.168.1.2", "txid": "ef56" * 16, "fee": 0.002},
    ]
    json_path.write_text(json.dumps(data))
    return json_path


@pytest.fixture
def sample_xml(tmp_path):
    xml_path = tmp_path / "test.xml"
    xml_path.write_text(
        '<?xml version="1.0"?>\n'
        "<transactions>\n"
        "  <transaction>\n"
        "    <timestamp>2024-09-01T00:00:00Z</timestamp>\n"
        "    <src_ip>192.168.1.1</src_ip>\n"
        "    <txid>abcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcdabcd</txid>\n"
        "    <fee>0.001</fee>\n"
        "  </transaction>\n"
        "</transactions>\n"
    )
    return xml_path


class TestFormatDetection:
    def test_detect_csv(self, sample_csv):
        assert detect_format(sample_csv) == "csv"

    def test_detect_json(self, sample_json):
        assert detect_format(sample_json) == "json"

    def test_detect_xml(self, sample_xml):
        assert detect_format(sample_xml) == "xml"


class TestCSVIngestion:
    def test_load_csv(self, sample_csv):
        df = load_csv(sample_csv)
        assert len(df) == 2
        assert "timestamp" in df.columns
        assert "src_ip" in df.columns

    def test_csv_adds_source_info(self, sample_csv):
        df = ingest(sample_csv)
        assert "source_file" in df.columns
        assert "original_row_number" in df.columns


class TestJSONIngestion:
    def test_load_json(self, sample_json):
        df = load_json(sample_json)
        assert len(df) == 2
        assert "timestamp" in df.columns


class TestXMLIngestion:
    def test_load_xml(self, sample_xml):
        df = load_xml(sample_xml)
        assert len(df) >= 1
        assert "timestamp" in df.columns


class TestEmptyFile:
    def test_empty_csv(self, tmp_path):
        empty = tmp_path / "empty.csv"
        empty.write_text("")
        with pytest.raises(Exception):
            load_csv(empty)

    def test_empty_json(self, tmp_path):
        empty = tmp_path / "empty.json"
        empty.write_text("[]")
        df = load_json(empty)
        assert len(df) == 0


class TestAutoIngest:
    def test_ingest_csv(self, sample_csv):
        df = ingest(sample_csv)
        assert len(df) == 2

    def test_ingest_json(self, sample_json):
        df = ingest(sample_json)
        assert len(df) == 2

    def test_ingest_xml(self, sample_xml):
        df = ingest(sample_xml)
        assert len(df) >= 1
