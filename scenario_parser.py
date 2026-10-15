#!/usr/bin/env python3

import os
import json
import uuid

MAX_CONNECTIONS = 500
MIN_HEADER_INTERVAL = 1
MAX_HEADER_INTERVAL = 30
MAX_DURATION = 300

ALLOWED_ATTACKERS = {"h1", "h2"}
ALLOWED_SERVERS = {"python", "php", "java"}

def validate_and_parse_scenario(raw_data):
    num_connections = raw_data.get("num_connections")
    header_interval = raw_data.get("header_interval")
    duration_s = raw_data.get("duration_s")
    attacker = raw_data.get("attacker", "h1")
    target_server = raw_data.get("target_server", "python")

    assert num_connections is not None, "[!] Fandango Constraint Error: Missing num_connections"
    assert header_interval is not None, "[!] Fandango Constraint Error: Missing header_interval"
    assert duration_s is not None, "[!] Fandango Constraint Error: Missing duration_s"

    assert 0 < num_connections <= MAX_CONNECTIONS, \
        f"[!] Python Safety Error: num_connections {num_connections} outside (0, {MAX_CONNECTIONS}]"
    assert MIN_HEADER_INTERVAL <= header_interval <= MAX_HEADER_INTERVAL, \
        f"[!] Python Safety Error: header_interval {header_interval} outside [{MIN_HEADER_INTERVAL}, {MAX_HEADER_INTERVAL}]"
    assert duration_s <= MAX_DURATION, \
        f"[!] Python Safety Error: Duration {duration_s} exceeds MAX_DURATION ({MAX_DURATION})"
    assert attacker in ALLOWED_ATTACKERS, \
        f"[!] Python Safety Error: attacker {attacker} not in {ALLOWED_ATTACKERS}"
    assert target_server in ALLOWED_SERVERS, \
        f"[!] Python Safety Error: target_server {target_server} not in {ALLOWED_SERVERS}"

    scenario_id = raw_data.get("id") or f"scenario_{uuid.uuid4().hex[:8]}"

    parsed_data = {
        "id": scenario_id,
        "num_connections": num_connections,
        "header_interval": header_interval,
        "attacker": attacker,
        "target_server": target_server,
        "duration": duration_s
    }

    return parsed_data

def save_scenario_to_json(scenario_data, output_path="scenarios/scenario_0001.json"):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(scenario_data, f, indent=2)
    return output_path
