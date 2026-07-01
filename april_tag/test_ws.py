from ws_server import BroadcastServer 
import json

# Usage
my_server = BroadcastServer()
my_server.start()

# Since the server is in a thread, we can do other things here
import time
try:
    data = { 'r': 0.0, 'p': 0.0, 'wz': 0.0 }
    while True:
        # You can trigger broadcasts from your main logic
        data['r'] += 0.05
        s = json.dumps(data)
        
        my_server.broadcast(s)
        time.sleep(0.1)
except KeyboardInterrupt:
    print("Shutting down.")
