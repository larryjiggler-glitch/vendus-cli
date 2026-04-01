"""Tests for output formatting."""

import json

from vendus_cli.format import output


def test_json_format():
    data = {"count": 5, "total": 100.50}
    result = output(data, fmt="json")
    parsed = json.loads(result)
    assert parsed == data


def test_table_format_list_of_dicts():
    data = [
        {"name": "Espresso", "qty": 10},
        {"name": "Latte", "qty": 5},
    ]
    result = output(data, fmt="table")
    assert "name" in result
    assert "Espresso" in result
    assert "Latte" in result
    lines = result.strip().split("\n")
    assert len(lines) == 4  # header + separator + 2 rows


def test_table_format_flat_dict():
    data = {"count": 5, "total": 100.50}
    result = output(data, fmt="table")
    assert "field" in result
    assert "count" in result
    assert "100.5" in result


def test_table_format_dict_with_list():
    data = {"categories": [{"id": 1, "title": "Coffee"}, {"id": 2, "title": "Tea"}]}
    result = output(data, fmt="table")
    assert "Coffee" in result
    assert "Tea" in result


def test_md_format():
    data = [{"name": "A", "value": 1}]
    result = output(data, fmt="md")
    assert result.startswith("| name")
    assert "| --- |" in result
    assert "| A | 1 |" in result


def test_empty_list():
    result = output([], fmt="table")
    assert "(no data)" in result
