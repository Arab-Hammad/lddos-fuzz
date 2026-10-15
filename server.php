<?php
error_reporting(E_ALL);
set_time_limit(0);

if (!function_exists('pcntl_fork')) {
    die("PCNTL functions not available on this PHP installation.\n");
}

$host = '0.0.0.0';
$port = isset($argv[1]) ? (int)$argv[1] : 8080;

$sock = socket_create(AF_INET, SOCK_STREAM, SOL_TCP);
if ($sock === false) {
    die("socket_create failed: " . socket_strerror(socket_last_error()) . "\n");
}

socket_set_option($sock, SOL_SOCKET, SO_REUSEADDR, 1);

if (socket_bind($sock, $host, $port) === false) {
    die("socket_bind failed: " . socket_strerror(socket_last_error()) . "\n");
}

if (socket_listen($sock, 1) === false) {
    die("socket_listen failed: " . socket_strerror(socket_last_error()) . "\n");
}

echo "VULNERABLE MULTI-PROCESS PHP LAB SERVER: Listening on http://$host:$port\n";
@ob_flush();
@flush();

pcntl_signal(SIGCHLD, SIG_IGN);

while (true) {
    $msgsock = socket_accept($sock);
    if ($msgsock === false) {
        continue;
    }

    socket_getpeername($msgsock, $client_ip, $client_port);

    $pid = pcntl_fork();

    if ($pid == -1) {
        socket_close($msgsock);
    } else if ($pid == 0) {
        socket_close($sock);

        socket_set_option($msgsock, SOL_SOCKET, SO_RCVTIMEO, array('sec' => 0, 'usec' => 0));
        socket_set_option($msgsock, SOL_SOCKET, SO_SNDTIMEO, array('sec' => 0, 'usec' => 0));

        echo "[+] New Slow Connection Received from IP: {$client_ip}:{$client_port} (PID: " . getmypid() . ")\n";
        @ob_flush();
        @flush();

        $request = "";
        while (true) {
            $buf = @socket_read($msgsock, 1024, PHP_NORMAL_READ);
            if ($buf === false || $buf === "") {
                break;
            }
            $request .= $buf;

            if (strpos($request, "\r\n\r\n") !== false) {
                $response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nSlow Server Response Active";
                @socket_write($msgsock, $response, strlen($response));
                break;
            }
        }

        echo "[-] Connection Closed for IP: {$client_ip}\n";
        @ob_flush();
        @flush();

        socket_close($msgsock);
        exit(0);
    } else {
        socket_close($msgsock);
    }
}

socket_close($sock);
?>
