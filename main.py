#!/usr/bin/env python3
import sys
from typing import Dict, List, Tuple, Set


def parse_input_file(path: str):
    """
    Parse the input file into:
      - station_chargers: dict[station_id] -> set[charger_id]
      - charger_reports: dict[charger_id] -> list[(start, end, up_bool)]
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines()]
    except OSError as e:
        # Couldn’t open file: treat as invalid input.
        print(f"Error: cannot open input file: {e}", file=sys.stderr)
        sys.exit(1)

    section = None
    station_chargers: Dict[int, Set[int]] = {}
    charger_reports: Dict[int, List[Tuple[int, int, bool]]] = {}

    for raw_line in lines:
        line = raw_line.strip()
        if not line:
            # ignore blank lines
            continue

        # Section headers
        if line.startswith("[") and line.endswith("]"):
            lower = line.lower()
            if lower == "[stations]":
                section = "stations"
            elif lower == "[charger availability reports]":
                section = "reports"
            else:
                # Unknown section: treat as invalid input
                print(f"Error: unknown section header: {line}", file=sys.stderr)
                sys.exit(1)
            continue

        if section == "stations":
            parts = line.split()
            if len(parts) < 2:
                # Station line must have at least 1 charger
                print(f"Error: invalid station line: {line}", file=sys.stderr)
                sys.exit(1)
            try:
                station_id = int(parts[0])
                charger_ids = [int(p) for p in parts[1:]]
            except ValueError:
                print(f"Error: non-integer in station line: {line}", file=sys.stderr)
                sys.exit(1)

            if station_id not in station_chargers:
                station_chargers[station_id] = set()
            station_chargers[station_id].update(charger_ids)

        elif section == "reports":
            parts = line.split()
            if len(parts) != 4:
                print(f"Error: invalid report line: {line}", file=sys.stderr)
                sys.exit(1)
            try:
                charger_id = int(parts[0])
                start = int(parts[1])
                end = int(parts[2])
            except ValueError:
                print(f"Error: non-integer in report line: {line}", file=sys.stderr)
                sys.exit(1)

            if end < start:
                print(f"Error: end time before start time in line: {line}", file=sys.stderr)
                sys.exit(1)

            up_str = parts[3].lower()
            if up_str not in ("true", "false"):
                print(f"Error: invalid up/down value in line: {line}", file=sys.stderr)
                sys.exit(1)
            up = (up_str == "true")

            charger_reports.setdefault(charger_id, []).append((start, end, up))

        else:
            # Line before any known section – ignore or treat as invalid.
            # Here we’ll just treat it as invalid to be strict.
            print(f"Error: content outside of a known section: {line}", file=sys.stderr)
            sys.exit(1)

    return station_chargers, charger_reports


def merge_intervals(intervals: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    """
    Given a list of [start, end) intervals (with start <= end),
    merge overlapping ones and return the merged list.
    """
    if not intervals:
        return []

    intervals = sorted(intervals, key=lambda x: (x[0], x[1]))
    merged: List[List[int]] = [list(intervals[0])]

    for start, end in intervals[1:]:
        last = merged[-1]
        if start > last[1]:
            # disjoint
            merged.append([start, end])
        else:
            # overlapping or touching; extend the last interval
            if end > last[1]:
                last[1] = end

    return [(s, e) for s, e in merged]


def compute_station_uptimes(
    station_chargers: Dict[int, Set[int]],
    charger_reports: Dict[int, List[Tuple[int, int, bool]]],
) -> Dict[int, int]:
    """
    For each station, compute the uptime percentage (0-100),
    rounded down to the nearest integer.
    """
    station_uptimes: Dict[int, int] = {}

    for station_id in sorted(station_chargers.keys()):
        chargers = station_chargers[station_id]

        # Collect all report entries and "up" intervals for this station’s chargers
        all_entries: List[Tuple[int, int]] = []
        up_intervals: List[Tuple[int, int]] = []

        for cid in chargers:
            for start, end, up in charger_reports.get(cid, []):
                all_entries.append((start, end))
                if up:
                    up_intervals.append((start, end))

        if not all_entries:
            # No data at all for this station’s chargers.
            station_uptimes[station_id] = 0
            continue

        # Time window for this station
        station_start = min(s for s, _ in all_entries)
        station_end = max(e for _, e in all_entries)
        total_span = station_end - station_start

        if total_span <= 0:
            station_uptimes[station_id] = 0
            continue

        # Sum union of up intervals
        merged_up = merge_intervals(up_intervals)
        up_time = sum(e - s for (s, e) in merged_up)

        # Floor to nearest integer percent
        uptime_pct = (up_time * 100) // total_span
        if uptime_pct < 0:
            uptime_pct = 0
        elif uptime_pct > 100:
            uptime_pct = 100

        station_uptimes[station_id] = uptime_pct

    return station_uptimes


def main(argv: List[str]) -> None:
    if len(argv) != 2:
        print(f"Usage: {argv[0]} <input_file>", file=sys.stderr)
        sys.exit(1)

    input_path = argv[1]
    station_chargers, charger_reports = parse_input_file(input_path)
    uptimes = compute_station_uptimes(station_chargers, charger_reports)

    # Print in ascending Station ID order
    for station_id in sorted(uptimes.keys()):
        print(f"{station_id} {uptimes[station_id]}")


if __name__ == "__main__":
    main(sys.argv)
