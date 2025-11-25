# charger-uptime
Coding challenge for Electric Era

# Overview

This project implements a solution to the Electric Era Coding Challenge, which computes station uptime based on charger availability reports. 

A station is considered up during any period where at least one of its chargers reports up = true.
Uptime is reported as an integer percentage between 0–100, rounded down (floor). 

This implementation is written fully in Python, is deterministic, and matches the example output provided in the challenge repository. 

# How to Run the Program

Run the solution from terminal:
``` python3 main.py input_1.txt ```

This will print:

``` 0 100 ```
``` 1 0   ```
``` 2 75  ```

# How to Run Tests

Install:

``` pip3 install pytest ```

Run test suite:

``` pytest -q ```


# Approach and Assumptions

1. Station Time Window

For each station:

``` station_start = min(start times from all reports for its chargers)
station_end   = max(end times from all reports for its chargers)
total_span    = station_end – station_start ```


All time outside reported intervals is considered downtime, per the specification.

2. Station Uptime Definition

For each station, collect all intervals across all its chargers where:

``` up == true ```

Then merge the overlapping intervals, compute the uptime, and compute percentage

``` uptime = floor( (total_up_time / total_span) * 100 ) ```

3. Chargers not listed under a station

If a charger appears in the [Charger Availability Reports] section but not in the [Stations] section: Its reports are ignored

4. Stations with no reports

If a station has charges defined but receives no reports: Its uptime is 0%

5. Overlapping intervals

Uptime intervals from chargers within a station are merged using standard interval-union logic.


# Algorithm Summary:

1. Parse input (stations + charger reports)

2. Build a charger_id → station_id mapping

3. For each station:

    - Track min start & max end times

    - Track only up=true intervals

4. Merge all up=true intervals

5. Compute:

    - total uptime

    - total time window

    - uptime percentage (floor)

6. Print results in ascending station order







