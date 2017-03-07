
from dschat.main import app


class ChatDaemon:
    def __init__(self):
        pass

    def run(self):
        app.run(host="0.0.0.0", debug=True)
