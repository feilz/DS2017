
from dschat.flask import app


class ChatDaemon:
    def __init__(self):
        print("Hellow rowld?")

    def run(self):
        app.run(host="0.0.0.0", debug=True)
