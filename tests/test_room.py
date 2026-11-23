import base64
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "chat"))
from webchat import Room, build_app


class RoomTest(unittest.TestCase):
    def setUp(self):
        self.password = "temporary-room-test"
        self.client = self.enterContext(TestClient(build_app(Room(self.password), "Test")))

    def connect(self, **options):
        socket = self.enterContext(self.client.websocket_connect("/ws"))
        socket.send_json({"type": "join", "password": self.password, "name": "Ala", **options})
        return socket, socket.receive_json()

    def test_invitation_and_envelope(self):
        first, created = self.connect(type="create")
        rid = created["room"]
        for invalid in [{"room": rid, "password": "wrong"}, {"room": "missing"}]:
            self.assertEqual(self.connect(**invalid)[1]["type"], "error")
        second, joined = self.connect(room=rid, name="Olek")
        self.assertEqual(joined["type"], "welcome")
        second.receive_json()
        self.assertEqual(second.receive_json()["users"], ["Ala", "Olek"])
        envelope = {field: base64.b64encode(os.urandom(n)).decode()
                    for field, n in [("iv", 12), ("ciphertext", 32)]}
        first.send_json({"text": "plaintext"})
        first.send_json(envelope)
        received = second.receive_json()
        self.assertEqual(received["ciphertext"], envelope["ciphertext"])
        self.assertNotIn("text", received)
        history = self.connect(room=rid, name="Ewa")[1]["history"]
        self.assertIn(received, history)
        self.assertEqual(self.connect(type="create", name="Ewa")[1]["history"], [])

    @patch("webchat.ROOM_DURATION", 0.1)
    def test_expiry_disconnects_and_invalidates_invitation(self):
        ws, created = self.connect(type="create", temporary=True)
        with self.assertRaises(WebSocketDisconnect) as closed:
            while True:
                ws.receive_json()
        self.assertEqual(closed.exception.code, 4001)
        self.assertEqual(self.connect(room=created["room"])[1]["type"], "error")
