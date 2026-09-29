"""Exercise the local server's trust boundary over actual HTTP connections."""

import http.client
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from aim_ui import AimUiError, AimUiServer, resolve_evidence_path


class LocalHttpTests(unittest.TestCase):
    def test_board_rejects_linked_root_and_recovers_without_restart(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            repo.mkdir()
            outside = root / "outside"
            outside.mkdir()
            (outside / "state.json").write_text('{"epicId":"outside-sentinel"}')
            workspace = repo / ".aim"
            workspace.symlink_to(outside, target_is_directory=True)
            server = AimUiServer(("127.0.0.1", 0), repo, ROOT / "aim-ui", quiet=True)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()

            def request():
                connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=3)
                try:
                    connection.request("GET", "/api/board")
                    response = connection.getresponse()
                    return response.status, response.read()
                finally:
                    connection.close()

            try:
                # No workspace reader should run through the rejected root.
                with patch("aim_ui._workspace_roots", side_effect=AssertionError("unsafe discovery")):
                    status, body = request()
                    self.assertEqual(status, 503)
                    self.assertNotIn(b"outside-sentinel", body)
                workspace.unlink()
                workspace.mkdir()
                self.assertEqual(request()[0], 200)
                # A broken link must be rejected as well as an existing target.
                workspace.rmdir()
                workspace.symlink_to(root / "missing", target_is_directory=True)
                self.assertEqual(request()[0], 503)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)

    def test_evidence_http_rejects_links_large_files_and_path_escape(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            repo = root / "repo"
            repo.mkdir()
            outside = root / "outside"
            outside.mkdir()
            (outside / "private.txt").write_text("outside-sentinel")
            (outside / "good.md").write_text("outside-sentinel")
            workspace = repo / ".aim"
            workspace.mkdir()
            (workspace / "good.md").write_text("safe evidence")
            (workspace / "large.md").write_bytes(b"x" * 1_000_001)
            (workspace / "linked").symlink_to(outside, target_is_directory=True)
            (workspace / "alias.md").symlink_to(workspace / "good.md")
            server = AimUiServer(("127.0.0.1", 0), repo, ROOT / "aim-ui", quiet=True)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()

            def request(path):
                connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=3)
                try:
                    connection.request("GET", f"/api/evidence?path={path}")
                    response = connection.getresponse()
                    return response.status, response.read()
                finally:
                    connection.close()

            try:
                self.assertEqual(request(".aim/good.md"), (200, b"safe evidence"))
                for path in (".aim/large.md", ".aim/linked/private.txt", ".aim/alias.md",
                             ".aim/%2e%2e/outside/private.txt"):
                    with self.subTest(path=path):
                        status, body = request(path)
                        self.assertEqual(status, 404)
                        self.assertNotIn(b"outside-sentinel", body)
                def replace_after_preflight(root, requested):
                    selected = resolve_evidence_path(root, requested)
                    workspace.rename(repo / "saved-aim")
                    workspace.symlink_to(outside, target_is_directory=True)
                    return selected

                with patch("aim_ui.resolve_evidence_path", side_effect=replace_after_preflight):
                    status, body = request(".aim/good.md")
                    self.assertEqual(status, 404)
                    self.assertNotIn(b"outside-sentinel", body)
                status, body = request(".aim/private.txt")
                self.assertEqual(status, 404)
                self.assertNotIn(b"outside-sentinel", body)
            finally:
                server.shutdown()
                server.server_close()
                thread.join(timeout=3)

    def test_server_cannot_bind_public_interfaces(self):
        with self.assertRaises(AimUiError):
            AimUiServer(("0.0.0.0", 0), ROOT, ROOT / "aim-ui")

    def test_rebinding_cross_origin_and_ambiguous_headers_are_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            server = AimUiServer(("127.0.0.1", 0), Path(directory), ROOT / "aim-ui", quiet=True)
            thread = threading.Thread(target=server.serve_forever, daemon=True)
            thread.start()
            port = server.server_address[1]
            host = f"127.0.0.1:{port}"
            cases = [
                ("GET", [("Host", host)], 200),
                ("GET", [("Host", f"localhost:{port}")], 200),
                ("GET", [("Host", f"attacker.example:{port}")], 403),
                ("GET", [("Host", "127.0.0.1:1")], 403),
                ("GET", [("Host", host), ("Origin", "https://attacker.example")], 403),
                ("GET", [("Host", host), ("Host", host)], 403),
                ("GET", [], 403),
                ("POST", [("Host", host)], 403),
                ("POST", [("Host", f"attacker.example:{port}"),
                           ("Origin", f"http://attacker.example:{port}")], 403),
                ("POST", [("Host", host), ("Origin", f"http://{host}"),
                           ("Origin", f"http://{host}")], 403),
                ("POST", [("Host", host), ("Origin", f"http://{host}")], 405),
            ]
            try:
                for method, headers, expected in cases:
                    with self.subTest(method=method, headers=headers):
                        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3)
                        try:
                            connection.putrequest(method, "/api/health", skip_host=True)
                            for key, value in headers:
                                connection.putheader(key, value)
                            connection.endheaders()
                            response = connection.getresponse()
                            self.assertEqual(response.status, expected)
                            body = response.read()
                            if expected == 403:
                                self.assertNotIn(directory.encode(), body)
                        finally:
                            connection.close()
            finally:
                server.shutdown(); server.server_close(); thread.join(timeout=3)


if __name__ == "__main__":
    unittest.main()
