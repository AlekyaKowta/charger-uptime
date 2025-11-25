import sys
from pathlib import Path

import pytest

# Adjust this import to your actual module name
from main import (
    parse_input_file,
    merge_intervals,
    compute_station_uptimes,
)

def write_input(tmp_path: Path, content: str) -> Path:
    """Helper to write an input file under a temporary directory."""
    p = tmp_path / "input.txt"
    p.write_text(content.strip() + "\n", encoding="utf-8")
    return p


# ---------- Unit tests for interval logic ----------


def test_merge_intervals_non_overlapping():
    intervals = [(0, 10), (20, 30)]
    merged = merge_intervals(intervals)
    assert merged == [(0, 10), (20, 30)]


def test_merge_intervals_overlapping():
    intervals = [(0, 10), (5, 15), (15, 20)]
    # (0,10) U (5,15) U (15,20) -> (0,20)
    merged = merge_intervals(intervals)
    assert merged == [(0, 20)]


def test_merge_intervals_mixed():
    intervals = [(10, 20), (0, 5), (5, 10), (30, 40)]
    # (0,5) U (5,10) U (10,20) -> (0,20), plus (30,40)
    merged = merge_intervals(intervals)
    assert merged == [(0, 20), (30, 40)]


# ---------- Unit tests for uptime computation ----------


def test_compute_station_uptimes_simple_single_station():
    # One station, id 0, total span [0, 30)
    station_ids = [0]
    station_min_max = {0: [0, 30]}

    # Up intervals: [0,10) and [20,30) -> total up = 20
    # Uptime = floor(20 * 100 / 30) = floor(66.66...) = 66
    station_up_intervals = {0: [(0, 10), (20, 30)]}

    uptimes = compute_station_uptimes(station_ids, station_min_max, station_up_intervals)
    assert uptimes == {0: 66}


def test_compute_station_uptimes_all_downtime():
    # One station with time window but no up intervals
    station_ids = [0]
    station_min_max = {0: [0, 100]}
    station_up_intervals = {0: []}

    uptimes = compute_station_uptimes(station_ids, station_min_max, station_up_intervals)
    assert uptimes == {0: 0}


def test_compute_station_uptimes_no_reports_for_station():
    # Station exists in [Stations] but no reports ever mention its chargers
    station_ids = [42]
    station_min_max = {}          # no entry for station 42
    station_up_intervals = {}     # no up intervals

    uptimes = compute_station_uptimes(station_ids, station_min_max, station_up_intervals)
    assert uptimes == {42: 0}


# ---------- Integration tests: parse + compute ----------


def test_example_input_1_matches_expected(tmp_path):
    """Full integration test based on the example from the challenge."""
    content = """
    [Stations]
    0 1001 1002
    1 1003
    2 1004

    [Charger Availability Reports]
    1001 0 50000 true
    1001 50000 100000 true
    1002 50000 100000 true
    1003 25000 75000 false
    1004 0 50000 true
    1004 100000 200000 true
    """

    input_path = write_input(tmp_path, content)

    station_ids, station_min_max, station_up_intervals = parse_input_file(str(input_path))
    uptimes = compute_station_uptimes(station_ids, station_min_max, station_up_intervals)

    # Expected from input_1_expected_stdout.txt:
    # 0 100
    # 1 0
    # 2 75
    assert uptimes[0] == 100
    assert uptimes[1] == 0
    assert uptimes[2] == 75
    # Also verify we have exactly these three stations
    assert set(uptimes.keys()) == {0, 1, 2}


def test_reports_for_unknown_charger_are_ignored(tmp_path):
    """
    If a charger appears in the report section but not in [Stations],
    it must be ignored.
    """
    content = """
    [Stations]
    0 1001

    [Charger Availability Reports]
    1001 0 100 true
    9999 0 100 false
    """

    input_path = write_input(tmp_path, content)

    station_ids, station_min_max, station_up_intervals = parse_input_file(str(input_path))
    uptimes = compute_station_uptimes(station_ids, station_min_max, station_up_intervals)

    # Only station 0's charger 1001 is relevant; it is up 100% of the time.
    assert station_ids == [0]
    assert uptimes == {0: 100}


def test_station_with_mixed_up_and_down_intervals(tmp_path):
    """
    More nuanced integration test: same station, 1 charger, mixed true/false.
    """
    content = """
    [Stations]
    0 1001

    [Charger Availability Reports]
    1001 0 10 true
    1001 10 20 false
    1001 20 40 true
    1001 40 50 false
    """

    # Total window: [0, 50) -> length 50
    # Up intervals: [0,10) and [20,40) -> total up = 10 + 20 = 30
    # Uptime = floor(30 * 100 / 50) = 60

    input_path = write_input(tmp_path, content)

    station_ids, station_min_max, station_up_intervals = parse_input_file(str(input_path))
    uptimes = compute_station_uptimes(station_ids, station_min_max, station_up_intervals)

    assert uptimes == {0: 60}
