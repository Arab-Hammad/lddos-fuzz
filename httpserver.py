import http.server
import socket
import socketserver
import sys

class HyperVulnerableHandler(http.server.SimpleHTTPRequestHandler):
    def handle(self):
        self.connection.settimeout(None)
        try:
            super().handle()
        except Exception:
            pass

class VulnerableHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    def server_bind(self):
        super().server_bind()
        self.socket.listen(1)

if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    server_address = ('0.0.0.0', port)

    vulnerable_server = VulnerableHTTPServer(server_address, HyperVulnerableHandler)

    print(f"VULNERABLE LAB SERVER: Listening on http://0.0.0.0:{port}")
    print("WARNING: This server is single-threaded per-connection-handling and will freeze "
          "if an exploit holds a connection open.")

    try:
        vulnerable_server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        vulnerable_server.server_close()
