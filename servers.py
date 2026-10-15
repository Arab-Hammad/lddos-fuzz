#!/usr/bin/env python3

JAVA_JAR_PATH = "/home/kali/vulnerable-java-server/target/vulnerable-server-1.0-SNAPSHOT.jar"
PHP_ENTRY_FILE = "/home/kali/server.php"
PYTHON_SERVER_SCRIPT = "/home/kali/httpserver.py"

SERVERS = {
    "python": {
        "port": 8080,
        "start_cmd": f"python3 {PYTHON_SERVER_SCRIPT} {{port}}",
        "pgrep_pattern": "httpserver.py",
    },
    "php": {
        "port": 8081,
        "start_cmd": f"php {PHP_ENTRY_FILE} {{port}}",
        "pgrep_pattern": "server.php",
    },
    "java": {
        "port": 8080,
        "start_cmd": f"java -jar {JAVA_JAR_PATH} {{port}}",
        "pgrep_pattern": "vulnerable-server",
    },
}

TOPOLOGY_IPS = {
    "h1": "10.0.0.1",
    "h2": "10.0.0.2",
    "h3": "10.0.0.3",
    "h4": "10.0.0.4",
    "h5": "10.0.0.5",
    "h6": "10.0.0.6",
}

SERVER_TO_HOST = {
    "python": "h4",
    "php": "h5",
    "java": "h6",
}


def start_server(host, server_type, max_wait=10, poll_interval=0.5):
    import time

    cfg = SERVERS[server_type]
    port = cfg["port"]
    pattern = cfg["pgrep_pattern"].format(port=port)

    host.cmd(f"pkill -9 -f '{pattern}' 2>/dev/null")
    host.cmd(f"fuser -k {port}/tcp 2>/dev/null")
    time.sleep(0.5)

    cmd = cfg["start_cmd"].format(port=port)
    host.cmd(f'{cmd} > /tmp/{server_type}_server.log 2>&1 &')

    pid = None
    elapsed = 0.0
    while elapsed < max_wait:
        time.sleep(poll_interval)
        elapsed += poll_interval
        pid_out = host.cmd(f"pgrep -o -f '{pattern}'").strip().split('\n')[0]
        if not pid_out:
            continue
        probe = host.cmd(
            f'curl -o /dev/null -s -w "%{{http_code}}" --max-time 2 '
            f'http://{host.IP()}:{port}/'
        ).strip()
        if probe and probe != "000":
            pid = pid_out
            break

    if not pid:
        log = host.cmd(f'tail -n 20 /tmp/{server_type}_server.log')
        raise RuntimeError(
            f"[!] {server_type} server on {host.name} did not answer within "
            f"{max_wait}s. Last log lines:\n{log}"
        )
    return pid, port


def stop_server(host, pid, max_wait=5, poll_interval=0.3, server_type=None):
    import time

    if not pid:
        return

    host.cmd(f'kill {pid} 2>/dev/null')
    elapsed = 0.0
    while elapsed < max_wait:
        still_alive = host.cmd(f'kill -0 {pid} 2>/dev/null; echo $?').strip()
        if still_alive.endswith('1'):
            break
        time.sleep(poll_interval)
        elapsed += poll_interval
    host.cmd(f'kill -9 {pid} 2>/dev/null')

    if server_type is not None:
        cfg = SERVERS[server_type]
        pattern = cfg["pgrep_pattern"].format(port=cfg["port"])
        host.cmd(f"pkill -9 -f '{pattern}' 2>/dev/null")
        host.cmd(f"fuser -k {cfg['port']}/tcp 2>/dev/null")
