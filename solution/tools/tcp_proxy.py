"""Tiny TCP relay used only when SSH GatewayPorts is unavailable.

Usage: python tcp_proxy.py LISTEN_PORT UPSTREAM_HOST UPSTREAM_PORT
The process keeps no request logs and stores no data.
"""

from __future__ import annotations

import selectors
import socket
import socketserver
import sys


class RelayHandler(socketserver.BaseRequestHandler):
    upstream_host = "127.0.0.1"
    upstream_port = 0

    def handle(self) -> None:
        with socket.create_connection((self.upstream_host, self.upstream_port)) as upstream:
            peers = {self.request: upstream, upstream: self.request}
            selector = selectors.DefaultSelector()
            for sock in peers:
                sock.setblocking(False)
                selector.register(sock, selectors.EVENT_READ)
            try:
                while True:
                    for key, _ in selector.select():
                        data = key.fileobj.recv(65536)
                        if not data:
                            return
                        peers[key.fileobj].sendall(data)
            finally:
                selector.close()


class RelayServer(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def main() -> None:
    if len(sys.argv) != 4:
        raise SystemExit("usage: tcp_proxy.py LISTEN_PORT UPSTREAM_HOST UPSTREAM_PORT")
    listen_port = int(sys.argv[1])
    RelayHandler.upstream_host = sys.argv[2]
    RelayHandler.upstream_port = int(sys.argv[3])
    with RelayServer(("0.0.0.0", listen_port), RelayHandler) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
