
from gevent import monkey
monkey.patch_all()

from threading import Thread
from flask import Flask, render_template, session, request, g
from flask_socketio import emit, join_room, leave_room, SocketIO, disconnect

from dschat.flask.app.routes import main
from dschat.daemon.connector import Connector
from dschat.util.timeutils import *
from dschat.db.database import Database


db = Database()

app = Flask(__name__)
app.debug = True
app.config["SECRET_KEY"] = "CHANGEME"
app.register_blueprint(main)
socketio = SocketIO(app)
thread = None


def background_thread():
    with Connector() as c:
        while True:
            print("here")
            c.connect()
            print("here")

            socketio.sleep(1)

            message = next(c.next_message())

            if message:
                with app.test_request_context('/'):
                    with app.app_context():
                        socketio.emit("message", message["content"], room=message["room"], namespace="/chat")


@socketio.on('joined', namespace='/chat')
def joined(message):
    """Sent by clients when they enter a room.
    A status message is broadcast to all people in the room."""
    room = session.get('room')
    join_room(room)
    username = session.get('name')
    tstamp = create_timestamp()
    datetime = ts_to_datetime(tstamp)
    unix_time = ts_to_unix(tstamp)
    message = ' has entered the room.'
    
    # TODO
    # Check if user exists
    # User session management... 
    if not db.user_exists(username):
        db.insert_user(user=username)
    
    # TODO
    # Synchronise messages here

    db.insert_message(user=username, ts=unix_time, message=message, room=room)
    
    emit('status', {'msg': datetime + ": " + username + message}, room=room)


@socketio.on('text', namespace='/chat')
def text(message):
    """Sent by a client when the user entered a new message.
    The message is sent to all people in the room."""
    room = session.get('room')
    username = session.get('name')
    tstamp = create_timestamp()
    datetime = ts_to_datetime(tstamp)
    unix_time = ts_to_unix(tstamp)
    message = message['msg']
    
    # TODO
    # Synchronise messages here

    db.insert_message(user=username, ts=unix_time, message=message, room=room)
    
    emit('message', {'msg': datetime + ": " + username + ':' + message}, room=room)


@socketio.on('left', namespace='/chat')
def left(message):
    """Sent by clients when they leave a room.
    A status message is broadcast to all people in the room."""
    room = session.get('room')
    username = session.get('name')
    tstamp = create_timestamp()
    datetime = ts_to_datetime(tstamp)
    unix_time = ts_to_unix(tstamp)
    message = ' has left the room.'
    leave_room(room)
    
    # TODO
    # Synchronise messages here

    db.insert_message(user=username, ts=unix_time, message=message, room=room)

    emit('status', {'msg': datetime + ": " + username + message}, room=room)


@socketio.on('connect', namespace='/chat')
def test_connect():
    global thread

    if not thread:
        thread = socketio.start_background_task(target=background_thread)
        #thread = Thread(target=background_thread)
        #thread.start()

    emit('my_response', {'data': 'Connected', 'count': 0})
