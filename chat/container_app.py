import os

from webchat import Room, build_app


def create_app():
    password = os.environ.get("CHAT_PASSWORD", "")
    if len(password) < 12:
        raise RuntimeError("CHAT_PASSWORD musi mieć przynajmniej 12 znaków.")
    return build_app(Room(password), "Wspólny czat", dashboard=True)
