#!/usr/bin/env python3

from mininet.net import Mininet
from mininet.node import OVSSwitch, RemoteController
from mininet.log import setLogLevel, info
import time
import csv
import os
import datetime

from servers import SERVERS, TOPOLOGY_IPS, SERVER_TO_HOST, start_server, stop_server
from metrics import collect_sample

NUM_RUNS_PER_SERVER = 5
CSV_FILE = "baseline_results.csv"
FIELDNAMES = ["experiment_id", "server_type", "timestamp", "attack",
              "service_up", "response_time_ms", "loss_pct",
              "throughput_Bps", "cpu_pct", "memory_kb"]


def build_topology():
    net = Mininet(switch=OVSSwitch, controller=RemoteController, autoSetMacs=True)
    net.addController('c0', controller=RemoteController, ip='127.0.0.1', port=6653)
    s1 = net.addSwitch('s1', protocols='OpenFlow13')

    hosts = {}
    for name, ip in TOPOLOGY_IPS.items():
        hosts[name] = net.addHost(name, ip=ip)
        net.addLink(hosts[name], s1)

    net.start()
    loss = net.pingAll(timeout='2')
    if loss > 0:
        info(f"[!] Warning: pingAll reported {loss}% loss before baseline collection started\n")

    return net, hosts


def run_baseline_for_server(net, hosts, server_type, experiment_id):
    victim_host_name = SERVER_TO_HOST[server_type]
    victim_host = hosts[victim_host_name]
    client_host = hosts['h3']

    info(f"[*] Starting {server_type} server on {victim_host_name}...\n")
    max_wait = 15 if server_type == "java" else 10
    pid, port = start_server(victim_host, server_type, max_wait=max_wait)

    try:
        timestamp = datetime.datetime.now().isoformat()
        sample = collect_sample(client_host, victim_host, victim_host.IP(), port, pid)
    finally:
        stop_server(victim_host, pid, server_type=server_type)

    return {
        "experiment_id": f"{experiment_id:03d}",
        "server_type": server_type,
        "timestamp": timestamp,
        "attack": "false",
        **sample
    }


if __name__ == '__main__':
    setLogLevel('info')

    file_exists = os.path.isfile(CSV_FILE)

    info("*** Starting Baseline Collection (no attack) across python/php/java servers ***\n")
    info("*** Make sure 'ryu-manager ryu.app.simple_switch_13' is already running on 127.0.0.1:6653 ***\n")

    net, hosts = build_topology()

    try:
        with open(CSV_FILE, mode='a', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            if not file_exists:
                writer.writeheader()

            exp_id = 1
            for server_type in SERVERS:
                for i in range(1, NUM_RUNS_PER_SERVER + 1):
                    info(f"[*] [{server_type}] Baseline run {i}/{NUM_RUNS_PER_SERVER} "
                         f"(experiment {exp_id})...\n")
                    result = run_baseline_for_server(net, hosts, server_type, exp_id)
                    writer.writerow(result)
                    f.flush()
                    info(f"[*] Recorded -> {result}\n")
                    exp_id += 1
                    time.sleep(0.5)
    finally:
        net.stop()

    info(f"*** Baseline collection complete. Saved to {CSV_FILE} ***\n")
