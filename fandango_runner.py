#!/usr/bin/env python3

import os
import json
import subprocess
from scenario_parser import validate_and_parse_scenario, save_scenario_to_json

NUM_SCENARIOS = 5

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def run_fandango_and_process():
    spec_path = os.path.join(PROJECT_ROOT, "spec", "lddos_scenario.fan")

    try:
        if os.path.exists(spec_path):
            result = subprocess.run(
                ["fandango", "fuzz", "-f", spec_path, "--format", "string", "-n", str(NUM_SCENARIOS)],
                capture_output=True,
                text=True,
                check=True,
                timeout=30
            )
            raw_output = result.stdout.strip()
            print(f"[*] Fandango Raw Output:\n{raw_output}\n")

            lines = [line.strip() for line in raw_output.split("\n") if line.strip()]

            if not lines:
                print("[X] Pipeline Error: fandango produced no output")
                return

            raw_scenarios = []
            for line in lines:
                try:
                    raw_scenarios.append(json.loads(line))
                except json.JSONDecodeError:
                    print(f"[!] Warning: skipping line that is not valid JSON: {line!r}")
        else:
            print(f"[!] Warning: {spec_path} not found, using fallback scenario")
            raw_scenarios = [{
                "id": "scenario_0001",
                "num_connections": 120,
                "header_interval": 10,
                "attacker": "h1",
                "target_server": "python",
                "duration_s": 30
            }]

        saved_count = 0
        for raw_data in raw_scenarios:
            try:
                validated_data = validate_and_parse_scenario(raw_data)
                out_path = os.path.join(PROJECT_ROOT, "scenarios", f"{validated_data['id']}.json")
                saved_path = save_scenario_to_json(validated_data, out_path)
                print(f"[+] Successfully generated and validated: {saved_path}")
                saved_count += 1
            except AssertionError as e:
                print(f"[!] Scenario rejected by validation: {e} (raw data: {raw_data})")

        print(f"[*] Done: {saved_count}/{len(raw_scenarios)} scenarios saved.")

    except subprocess.TimeoutExpired:
        print("[X] Pipeline Error: fandango timed out")
    except Exception as e:
        print(f"[X] Pipeline Error: {e}")

if __name__ == "__main__":
    run_fandango_and_process()
