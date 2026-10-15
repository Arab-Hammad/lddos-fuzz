#!/usr/bin/env python3

import time


def check_service(client_host, victim_ip, port, path="/", timeout=5, debug=False):
    curl_out = client_host.cmd(
        f'curl -o /dev/null -s -w "%{{http_code}},%{{time_total}}" '
        f'--max-time {timeout} http://{victim_ip}:{port}{path}'
    )
    if debug:
        print(f"[DEBUG check_service] raw curl output: {curl_out!r}")
    try:
        code, t_total = curl_out.strip().split(',')
        if code.startswith('2') or code.startswith('3'):
            return True, round(float(t_total) * 1000.0, 2)
        elif debug:
            print(f"[DEBUG check_service] non-2xx/3xx http_code: {code!r}")
    except (ValueError, IndexError) as e:
        if debug:
            print(f"[DEBUG check_service] failed to parse curl output: {e}")
    return False, 0.0


def measure_loss(client_host, victim_ip, count=3):
    ping_out = client_host.cmd(f'ping -c {count} -W 1 {victim_ip}')
    loss = 100.0
    for line in ping_out.split('\n'):
        if 'packet loss' in line:
            for part in line.split(','):
                if 'packet loss' in part:
                    try:
                        loss = float(part.strip().split('%')[0].strip())
                    except ValueError:
                        pass
    return loss


def measure_throughput(client_host, victim_ip, port, path="/"):
    curl_out = client_host.cmd(
        f'curl -o /dev/null -s -w "%{{speed_download}}" '
        f'--max-time 5 http://{victim_ip}:{port}{path}'
    )
    try:
        return float(curl_out.strip())
    except ValueError:
        return 0.0


def measure_resource_usage_ps(victim_host, pid):
    if not pid:
        return 0.0, 0.0

    out = victim_host.cmd(f'ps -o %cpu=,%mem= --pid {pid} 2>/dev/null').strip()
    if not out:
        out = victim_host.cmd(f'ps --ppid {pid} -o %cpu=,%mem= 2>/dev/null').strip()

    cpu_pct = 0.0
    mem_kb = 0.0

    try:
        if out:
            lines = out.split('\n')
            total_cpu = 0.0
            for line in lines:
                parts = line.strip().split()
                if len(parts) >= 1:
                    total_cpu += float(parts[0])
            cpu_pct = round(total_cpu, 2)
    except (ValueError, IndexError):
        cpu_pct = 0.0

    status_out = victim_host.cmd(f'grep VmRSS /proc/{pid}/status 2>/dev/null').strip()
    if status_out:
        try:
            mem_kb = float(status_out.split()[1])
        except (IndexError, ValueError):
            mem_kb = 0.0

    return cpu_pct, mem_kb


def collect_sample(client_host, victim_host, victim_ip, port, victim_pid, path="/", debug=False):
    service_up, response_time_ms = check_service(client_host, victim_ip, port, path, debug=debug)
    throughput_Bps = measure_throughput(client_host, victim_ip, port, path)
    
    cpu_pct, memory_kb = measure_resource_usage_ps(victim_host, victim_pid)
    
    loss_pct = measure_loss(client_host, victim_ip)

    return {
        "service_up": int(service_up),
        "response_time_ms": response_time_ms,
        "loss_pct": loss_pct,
        "throughput_Bps": round(throughput_Bps, 2),
        "cpu_pct": cpu_pct,
        "memory_kb": memory_kb,
    }
