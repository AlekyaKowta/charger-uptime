#!/usr/bin/env python3
import sys
from typing import Dict, List, Tuple


def parse_input_file(path: str):
    """
    Parse file into:
      - station_ids: sorted list of station IDs
      - charger_to_station: charger_id -> station_id
      - station_min_max: station_id -> [min_time, max_time]
      - station_up_intervals: station_id -> list[(start, end)]
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f]
    except OSError as e:
        print(f"Error: cannot open input file: {e}", file=sys.stderr)
        sys.exit(1)

    section = None
    charger_to_station: Dict[int, int] = {}
    station_ids = set()

    # These are filled while parsing reports
    station_min_max: Dict[int, List[int]] = {}        # station_id -> [min_time, max_time]
    station_up_intervals: Dict[int, List[Tuple[int, int]]] = {}  # station_id -> up intervals

    i = 0
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        if not line:
            continue

        if line.startswith("[") and line.endswith("]"):
            lower = line.lower()
            if lower == "[stations]":
                section = "stations"
            elif lower == "[charger availability reports]":
                section = "reports"
            else:
                print(f"Error: unknown section header: {line}", file=sys.stderr)
                sys.exit(1)
            continue

        if section == "stations":
            parts = line.split()
            if len(parts) < 2:
                print(f"Error: invalid station line: {line}", file=sys.stderr)
                sys.exit(1)
            try:
                station_id = int(parts[0])
                charger_ids = [int(p) for p in parts[1:]]
            except ValueError:
                print(f"Error: non-integer in station line: {line}", file=sys.stderr)
                sys.exit(1)

            if station_id in station_ids:
                print(f"Error: duplicate station ID: {station_id}", file=sys.stderr)
                sys.exit(1)

            station_ids.add(station_id)

            for cid in charger_ids:
                if cid in charger_to_station:
                    # per preconditions this shouldn't happen
                    print(f"Error: charger {cid} assigned to multiple stations", file=sys.stderr)
                    sys.exit(1)
                charger_to_station[cid] = station_id

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

            # Map charger -> station; ignore reports for chargers not in [Stations]
            station_id = charger_to_station.get(charger_id)
            if station_id is None:
                continue

            # Update station time bounds
            if station_id not in station_min_max:
                station_min_max[station_id] = [start, end]
            else:
                mm = station_min_max[station_id]
                if start < mm[0]:
                    mm[0] = start
                if end > mm[1]:
                    mm[1] = end

            # Store only up=true intervals
            if up:
                station_up_intervals.setdefault(station_id, []).append((start, end))

        else:
            print(f"Error: content outside of a known section: {line}", file=sys.stderr)
            sys.exit(1)

    return sorted(station_ids), station_min_max, station_up_intervals


def merge_intervals(intervals: List[Tuple[int, int]]) -> List[Tuple[int, int]]:
    if not intervals:
        return []

    intervals = sorted(intervals, key=lambda x: (x[0], x[1]))
    merged: List[List[int]] = [list(intervals[0])]

    for start, end in intervals[1:]:
        last = merged[-1]
        if start > last[1]:
            merged.append([start, end])
        else:
            if end > last[1]:
                last[1] = end

    return [(s, e) for s, e in merged]


def compute_station_uptimes(
    station_ids: List[int],
    station_min_max: Dict[int, List[int]],
    station_up_intervals: Dict[int, List[Tuple[int, int]]],
) -> Dict[int, int]:
    uptimes: Dict[int, int] = {}

    for sid in station_ids:
        mm = station_min_max.get(sid)
        if not mm:
            # No reports at all for this station
            uptimes[sid] = 0
            continue

        start, end = mm
        total_span = end - start
        if total_span <= 0:
            uptimes[sid] = 0
            continue

        ups = station_up_intervals.get(sid, [])
        merged = merge_intervals(ups)
        up_time = sum(e - s for (s, e) in merged)

        pct = (up_time * 100) // total_span
        if pct < 0:
            pct = 0
        elif pct > 100:
            pct = 100

        uptimes[sid] = pct

    return uptimes


def main(argv):
    if len(argv) != 2:
        print(f"Usage: {argv[0]} <input_file>", file=sys.stderr)
        sys.exit(1)

    station_ids, station_min_max, station_up_intervals = parse_input_file(argv[1])
    uptimes = compute_station_uptimes(station_ids, station_min_max, station_up_intervals)

    for sid in station_ids:
        print(f"{sid} {uptimes.get(sid, 0)}")


if __name__ == "__main__":
    main(sys.argv)
