from flask import Flask
from flask_socketio import SocketIO
from main import main2 as main_blueprint
socketio = SocketIO()


def create_app(debug=False):
    """Create an application."""
    app = Flask(__name__)
    app.debug = debug
    app.config['SECRET_KEY'] = 'gjr39dkjn344_!67#'

    
    app.register_blueprint(main_blueprint)

    socketio.init_app(app)
    return app

