"""Run: python -m unittest discover -s tests (requires fastapi[standard] or httpx)."""
import sys
import unittest
from pathlib import Path

from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "chat"))
from webchat import Room, build_app


class RoomTest(unittest.TestCase):
    def test_login_presence_messages_and_rejoin(self):
        password = "temporary-room-test"
        app = build_app(Room(password), "Test", dashboard=True)
        with TestClient(app) as client:
            def join(ws, name):
                ws.send_json({"type": "auth", "name": name, "password": password})
                welcome = ws.receive_json()
                self.assertEqual(welcome["type"], "welcome")
                return welcome["history"]

            with client.websocket_connect("/ws") as first:
                join(first, "Ala")
                with client.websocket_connect("/ws") as second:
                    join(second, "Olek")
                    self.assertEqual(second.receive_json()["type"], "system")
                    self.assertEqual(second.receive_json()["users"], ["Ala", "Olek"])
                    first.send_json({"text": "Cześć!"})
                    self.assertEqual(second.receive_json()["text"], "Cześć!")
                with client.websocket_connect("/ws") as rejoined:
                    history = join(rejoined, "Olek")
                    self.assertIn("Cześć!", [entry["text"] for entry in history])
