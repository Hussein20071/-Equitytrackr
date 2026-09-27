"""HTTP server entry point with a singleton kernel-mutex guard.

Same discipline as the refresh loop: the child process owns the mutex for
its lifetime, so duplicate spawns self-eliminate regardless of how they
were started. Run via: python -m tracker.serve
"""
import sys

from .single_instance import acquire


def main() -> int:
    if not acquire("FreebuffTrackerServe"):
        print("another preview server is already running -- exiting")
        return 0
    import http.server
    import socketserver
    import functools

    class _Server(socketserver.TCPServer):
        allow_reuse_address = True

    handler = functools.partial(
        http.server.SimpleHTTPRequestHandler, directory="publish")
    with _Server(("", 8123), handler) as httpd:
        print("serving publish/ on http://127.0.0.1:8123")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
