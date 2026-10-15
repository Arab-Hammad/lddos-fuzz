#!/usr/bin/env python3

import os
import sys
import json
import time
import argparse
from mininet.net import Mininet
from mininet.node import OVSSwitch, RemoteController
from mininet.log import setLogLevel, info

from traffic import start_slowloris_attack, stop_slowloris_attack, validate_scenario
from servers import SERVERS, TOPOLOGY_IPS, SERVER_TO_HOST, start_server, stop_server
from metrics import collect_sample

def load_scenario(scenario_path):
    if not os.path.exists(scenario_path):
        print(f"[X] Error: Scenario file not found at {scenario_path}")
        sys.exit(1)
    with open(scenario_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def setup_experiment_directory(scenario_id):
    output_dir = os.path.join("results", scenario_id)
    os.makedirs(output_dir, exist_ok=True)
    return output_dir

def run_experiment(scenario_path):
    scenario = load_scenario(scenario_path)
    scenario_id = scenario["id"]
    output_dir = setup_experiment_directory(scenario_id)

    with open(os.path.join(output_dir, "scenario.json"), 'w', encoding='utf-8') as f:
        json.dump(scenario, f, indent=4)

    info(f"[*] Starting experiment for {scenario_id}\n")
    info("[*] Make sure 'ryu-manager ryu.app.simple_switch_13' is already running on 127.0.0.1:6653\n")

    setLogLevel('info')

    validate_scenario(scenario)

    net = Mininet(switch=OVSSwitch, controller=RemoteController, autoSetMacs=True)
    victim_pid = None
    legit_pid = None
    attack_pid = None

    try:
        info("[*] Configuring network topology (2 attackers, 1 legit client, 3 victim servers)...\n")
        net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6653)
        s1 = net.addSwitch('s1', protocols='OpenFlow13')

        hosts = {}
        for name, ip in TOPOLOGY_IPS.items():
            hosts[name] = net.addHost(name, ip=ip)
            net.addLink(hosts[name], s1)

        net.start()

        loss = net.pingAll(timeout='2')
        if loss > 0:
            info(f"[!] Warning: pingAll reported {loss}% loss before the experiment started\n")

        attacker_name = scenario["attacker"]
        target_server = scenario["target_server"]
        victim_host_name = SERVER_TO_HOST[target_server]

        h_attacker = hosts[attacker_name]
        h_victim = hosts[victim_host_name]
        h_legit = hosts['h3']

        info(f"[*] Attacker: {attacker_name} -> Target server: {target_server} ({victim_host_name})\n")

        info(f"[*] Starting {target_server} victim service on {victim_host_name}...\n")
        victim_pid, target_port = start_server(h_victim, target_server)

        info("[*] Starting legitimate traffic...\n")
        h_legit.cmd(f'ping -i 1 {h_victim.IP()} > {output_dir}/legit_ping.log 2>&1 &')
        legit_pid = h_legit.cmd("pgrep -f 'ping -i 1'").strip().split('\n')[0]

        duration = scenario["duration"]
        info(f"[*] Launching Slowloris attack from {attacker_name} (Duration: {duration}s)...\n")
        attack_pid = start_slowloris_attack(h_attacker, h_victim.IP(), target_port, scenario)

        metrics_csv_path = os.path.join(output_dir, "metrics.csv")
        start_time = time.time()
        sample_interval = 2

        fieldnames = ["timestamp", "service_up", "response_time_ms",
                      "loss_pct", "throughput_Bps", "cpu_pct", "memory_kb"]

        with open(metrics_csv_path, 'w', encoding='utf-8') as metrics_file:
            metrics_file.write(",".join(fieldnames) + "\n")

            while (time.time() - start_time) < duration:
                time.sleep(sample_interval)
                current_time = round(time.time() - start_time, 2)

                sample = collect_sample(h_legit, h_victim, h_victim.IP(), target_port, victim_pid)

                row = [str(current_time)] + [str(sample[k]) for k in fieldnames[1:]]
                metrics_file.write(",".join(row) + "\n")

        info("[*] Stopping everything and cleaning up...\n")

        summary_data = {
            "scenario_id": scenario_id,
            "attacker": attacker_name,
            "target_server": target_server,
            "status": "completed",
            "total_duration_s": duration,
            "metrics_collected": True
        }
        with open(os.path.join(output_dir, "summary.json"), 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, indent=4)

        info(f"[*] Experiment results successfully saved in: {output_dir}\n")

    except Exception as e:
        print(f"[X] Experiment Error: {e}")
    finally:
        if attack_pid:
            stop_slowloris_attack(h_attacker, attack_pid)
        if victim_pid:
            stop_server(h_victim, victim_pid, server_type=target_server)
        if legit_pid:
            h_legit.cmd(f'kill {legit_pid} 2>/dev/null')
        net.stop()
        os.system('sudo mn -c > /dev/null 2>&1')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run LDDoS SDN Experiment in Mininet")
    parser.add_argument("--scenario", required=True, help="Path to scenario JSON file")
    args = parser.parse_args()

    run_experiment(args.scenario)
