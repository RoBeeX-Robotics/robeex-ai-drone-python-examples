import threading
from typing import Union
from websocket_server import WebsocketServer
import json

class BroadcastServer:
    def __init__(self, port: int, host='127.0.0.1'):
        self.host = host
        self.port = port
        self.server = WebsocketServer(host=self.host, port=self.port)
        
        # Set up callbacks
        self.server.set_fn_new_client(self._new_client)
        self.server.set_fn_client_left(self._client_left)
        self.server.set_fn_message_received(self._message_received)
        
        # Start the server in a background daemon thread
        self.thread = threading.Thread(target=self.server.run_forever, daemon=True)

    def start(self):
        """Starts the server thread."""
        print(f"Starting threaded server on {self.host}:{self.port}...")
        self.thread.start()

    def broadcast(self, message):
        """Send a message to all connected clients."""
        # print(f"Broadcasting: {message}")
        self.server.send_message_to_all(message)
        
    def broadcast_json(self, message: Union[dict, list]):
        """Send a message to all connected clients."""
        self.server.send_message_to_all(json.dumps(message))

    # --- Internal Callbacks ---
    def _new_client(self, client, server):
        print(f"Client {client['id']} connected.")

    def _client_left(self, client, server):
        print(f"Client {client['id']} disconnected.")

    def _message_received(self, client, server, message):
        print(f"Client {client['id']} sent: {message}")
        # Example: broadcast incoming messages to everyone
        self.broadcast(f"User {client['id']} says: {message}")

if __name__ == "__main__":
    # Usage
    my_server = BroadcastServer()
    my_server.start()

    # Since the server is in a thread, we can do other things here
    import time
    try:
        while True:
            # You can trigger broadcasts from your main logic
            # my_server.broadcast("Heartbeat from main thread")
            time.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down.")
