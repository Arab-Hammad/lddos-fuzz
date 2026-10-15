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


def _cpu_time_ns(victim_host, pid):
    out = victim_host.cmd(f'cat /proc/{pid}/schedstat 2>/dev/null').strip()
    if out:
        try:
            return int(out.split()[0])
        except (IndexError, ValueError):
            pass

    out = victim_host.cmd(f'cat /proc/{pid}/stat 2>/dev/null').strip()
    if not out:
        return None
    fields = out.split()
    try:
        return (int(fields[13]) + int(fields[14])) * 10_000_000
    except (IndexError, ValueError):
        return None


def measure_resource_usage(victim_host, pid, during=None, sample_time=0.2):
    if not pid:
        return 0.0, 0.0

    t0 = _cpu_time_ns(victim_host, pid)
    if t0 is None:
        return 0.0, 0.0

    start = time.time()
    if during is not None:
        during()
    else:
        time.sleep(sample_time)
    elapsed = max(time.time() - start, 0.001)

    t1 = _cpu_time_ns(victim_host, pid)
    cpu_pct = 0.0
    if t1 is not None:
        cpu_pct = ((t1 - t0) / 1e9) / elapsed * 100.0

    mem_kb = 0.0
    status_out = victim_host.cmd(f'grep VmRSS /proc/{pid}/status 2>/dev/null').strip()
    if status_out:
        try:
            mem_kb = float(status_out.split()[1])
        except (IndexError, ValueError):
            pass

    return round(cpu_pct, 2), mem_kb


def collect_sample(client_host, victim_host, victim_ip, port, victim_pid, path="/", debug=False):
    result = {}

    def during():
        result["service_up"], result["response_time_ms"] = check_service(
            client_host, victim_ip, port, path, debug=debug
        )
        result["throughput_Bps"] = measure_throughput(client_host, victim_ip, port, path)

    cpu_pct, memory_kb = measure_resource_usage(victim_host, victim_pid, during=during)
    loss_pct = measure_loss(client_host, victim_ip)

    return {
        "service_up": int(result.get("service_up", False)),
        "response_time_ms": result.get("response_time_ms", 0.0),
        "loss_pct": loss_pct,
        "throughput_Bps": round(result.get("throughput_Bps", 0.0), 2),
        "cpu_pct": cpu_pct,
        "memory_kb": memory_kb,
    }
