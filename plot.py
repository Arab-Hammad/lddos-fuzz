#!/usr/bin/env python3

import sys
import os
import csv
import matplotlib.pyplot as plt

BASELINE_CSV = "baseline_results.csv"
OUTPUT_DIR = "plots"


def read_csv(path):
    with open(path, newline='') as f:
        return list(csv.DictReader(f))


def plot_baseline(rows):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    servers = sorted(set(r["server_type"] for r in rows))

    metrics = [
        ("response_time_ms", "Response Time (ms)"),
        ("cpu_pct", "CPU Usage (%)"),
        ("memory_kb", "Memory (KB)"),
        ("throughput_Bps", "Throughput (Bytes/sec)"),
    ]

    for metric_key, metric_label in metrics:
        fig, ax = plt.subplots()
        for server in servers:
            values = [float(r[metric_key]) for r in rows if r["server_type"] == server]
            ax.plot(range(1, len(values) + 1), values, marker='o', label=server)
        ax.set_xlabel("Run #")
        ax.set_ylabel(metric_label)
        ax.set_title(f"Baseline: {metric_label} per server (no attack)")
        ax.legend()
        fig.tight_layout()
        out_path = os.path.join(OUTPUT_DIR, f"baseline_{metric_key}.png")
        fig.savefig(out_path)
        print(f"[+] Saved {out_path}")
        plt.close(fig)

    fig, ax = plt.subplots()
    availability = []
    for server in servers:
        vals = [int(r["service_up"]) for r in rows if r["server_type"] == server]
        availability.append(100.0 * sum(vals) / len(vals) if vals else 0.0)
    ax.bar(servers, availability)
    ax.set_ylabel("Service Availability (%)")
    ax.set_title("Baseline: Service Availability per server (no attack)")
    ax.set_ylim(0, 105)
    fig.tight_layout()
    out_path = os.path.join(OUTPUT_DIR, "baseline_availability.png")
    fig.savefig(out_path)
    print(f"[+] Saved {out_path}")
    plt.close(fig)


def plot_attack(rows, scenario_id):
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    timestamps = [float(r["timestamp"]) for r in rows]

    metrics = [
        ("response_time_ms", "Response Time (ms)"),
        ("service_up", "Service Available (1=up, 0=down)"),
        ("cpu_pct", "CPU Usage (%)"),
        ("memory_kb", "Memory (KB)"),
        ("loss_pct", "Packet Loss (%)"),
    ]

    for metric_key, metric_label in metrics:
        values = [float(r[metric_key]) for r in rows]
        fig, ax = plt.subplots()
        ax.plot(timestamps, values, marker='o', color='crimson')
        ax.set_xlabel("Time since attack start (s)")
        ax.set_ylabel(metric_label)
        ax.set_title(f"{scenario_id}: {metric_label} during attack")
        fig.tight_layout()
        out_path = os.path.join(OUTPUT_DIR, f"{scenario_id}_{metric_key}.png")
        fig.savefig(out_path)
        print(f"[+] Saved {out_path}")
        plt.close(fig)


if __name__ == "__main__":
    if not os.path.isfile(BASELINE_CSV):
        print(f"[X] {BASELINE_CSV} not found. Run mininet_topology.py first.")
        sys.exit(1)

    baseline_rows = read_csv(BASELINE_CSV)
    plot_baseline(baseline_rows)

    if len(sys.argv) > 1:
        scenario_dir = sys.argv[1]
        metrics_path = os.path.join(scenario_dir, "metrics.csv")
        scenario_id = os.path.basename(scenario_dir.rstrip('/'))
        if not os.path.isfile(metrics_path):
            print(f"[X] {metrics_path} not found.")
            sys.exit(1)
        attack_rows = read_csv(metrics_path)
        plot_attack(attack_rows, scenario_id)

    print(f"[*] Done. Charts saved in ./{OUTPUT_DIR}/")
