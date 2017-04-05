
from gevent import monkey
monkey.patch_all()

import json
from threading import Thread
from flask import Flask, render_template, session, request, g
from flask_socketio import emit, join_room, leave_room, SocketIO, disconnect

from dschat.flask.app.routes import main
from dschat.daemon.connector import Connector
from dschat.util.timeutils import *
from dschat.db.database import Database
from dschat.util.crypto import *


db = Database()

app = Flask(__name__)
app.config["SECRET_KEY"] = "CHANGEME"
app.register_blueprint(main)
socketio = SocketIO(app)
thread = None

c = None


def background_thread():
    global c
    if not c:
        print("here")
        c = Connector()
        print("where")
        c.connect()

    print("there")
    while True:
        socketio.sleep(1)

        while True:
            payload = next(c.next_message())
            if payload:
                payload = payload.split('|')
                message = json.loads(decrypt(payload[0], c.secret))
                digest = decrypt(payload[1], c.secret)
                if verify(json.dumps(message), digest):
                    with app.app_context():
                        new_message = "%s: %s: %s" % (ts_to_date(message["timestamp"]), message["username"], message["message"])
                        socketio.emit("message", {"msg": new_message}, room=message["room"], namespace="/chat")
                else:
                    break
            else:
                break


@socketio.on('joined', namespace='/chat')
def joined(message):
    """Sent by clients when they enter a room.
    A status message is broadcast to all people in the room."""
    room = session.get('room')
    join_room(room)
    username = session.get('name')
    unix_time = create_timestamp()
    datetime = ts_to_date(unix_time)
    status_message = ' has entered the room.'

    # TODO
    # Check ZMQ buffer for newer messages
    # that have not been emitted
    
    if c:
        while True:
            payload = next(c.next_message())
            if payload:
                payload = payload.split('|')
                message = json.loads(decrypt(payload[0], c.secret))
                digest = decrypt(payload[1], c.secret)
                if verify(json.dumps(message), digest) and message["timestamp"] < unix_time:
                    new_message = "%s: %s: %s" % (ts_to_date(message["timestamp"]), message["username"], message["message"])
                    emit("message", {"msg": new_message}, room=message["room"])
                else:
                    break
            else:
                break
    
    
    # TODO
    # Check if user exists
    # User session management... 
    if not db.user_exists(username):
        db.insert_user(user=username)
    
    # TODO
    # Synchronise messages here
    if c:
        json_string = {
            'username': username,
            'timestamp': unix_time,
            'message': status_message,
            'room': room,
        }
        encrypted_json = encrypt(json.dumps(json_string), c.secret)
        encrypted_digest = encrypt(sha1(json.dumps(json_string)), c.secret)
        c.zmq.publish(encrypted_json + "|" + encrypted_digest)

    #Insert data to local database
    db.insert_message(user=username, ts=unix_time, message=status_message, room=room)
    
    emit('status', {'msg': datetime + ": " + username + status_message}, room=room)


@socketio.on('text', namespace='/chat')
def text(message):
    """Sent by a client when the user entered a new message.
    The message is sent to all people in the room."""
    room = session.get('room')
    username = session.get('name')
    unix_time = create_timestamp()
    datetime = ts_to_date(unix_time)
    status_message = message['msg']
    
    # TODO
    # Check ZMQ buffer for newer messages
    # that have not been emitted
    while True:
        payload = next(c.next_message())
        if payload:
            payload = payload.split('|')
            message = json.loads(decrypt(payload[0], c.secret))
            digest = decrypt(payload[1], c.secret)
            if verify(json.dumps(message), digest) and message["timestamp"] < unix_time:
                new_message = "%s: %s: %s" % (ts_to_date(message["timestamp"]), message["username"], message["message"])
                emit("message", {"msg": new_message}, room=message["room"])
            else:
                break
        else:
            break
                
    # TODO
    # Synchronise messages here
    json_string = {
        'username': username,
        'timestamp': unix_time,
        'message': status_message,
        'room': room,
    }
    encrypted_json = encrypt(json.dumps(json_string), c.secret)
    encrypted_digest = encrypt(sha1(json.dumps(json_string)), c.secret)
    c.zmq.publish(encrypted_json + "|" + encrypted_digest)

    #Insert data to local database
    db.insert_message(user=username, ts=unix_time, message=status_message, room=room)
    
    emit('message', {'msg': datetime + ": " + username + ':' + status_message}, room=room)


@socketio.on('left', namespace='/chat')
def left(message):
    """Sent by clients when they leave a room.
    A status message is broadcast to all people in the room."""
    room = session.get('room')
    username = session.get('name')
    session["left"] = True
    unix_time = create_timestamp()
    datetime = ts_to_date(unix_time)
    status_message = ' has left the room.'
    leave_room(room)
    
    # TODO
    # Check ZMQ buffer for newer messages
    # that have not been emitted

    zmq_buffer = next(c.next_message())
    
    if zmq_buffer:
        zmq_timestamp = zmq_buffer["timestamp"]

        if zmq_timestamp < unix_time:
            emit("message", {"msg": message["data"]}, room=message["room"], namespace="/chat")    

    while True:
        payload = next(c.next_message())
        if payload:
            payload = payload.split('|')
            message = json.loads(decrypt(payload[0], c.secret))
            digest = decrypt(payload[1], c.secret)
            if verify(json.dumps(message), digest) and message["timestamp"] < unix_time:
                new_message = "%s: %s: %s" % (ts_to_date(message["timestamp"]), message["username"], message["message"])
                emit("message", {"msg": new_message}, room=message["room"])
            else:
                break
        else:
            break

    # TODO
    # Synchronise messages here
    json_string = {
        'username': username,
        'timestamp': unix_time,
        'message': status_message,
        'room': room,
    }
    encrypted_json = encrypt(json.dumps(json_string), c.secret)
    encrypted_digest = encrypt(sha1(json.dumps(json_string)), c.secret)
    c.zmq.publish(encrypted_json + "|" + encrypted_digest)
    
    #Insert data to local database
    db.insert_message(user=username, ts=unix_time, message=status_message, room=room)

    emit('status', {'msg': datetime + ": " + username + status_message}, room=room)

@socketio.on('disconnect', namespace='/chat')
def disconnected():
    """Called when client is disconnected by accident or by browser closing."""
    if session.get('left') is None:
        room = session.get('room')
        username = session.get('name')
        unix_time = create_timestamp()
        datetime = ts_to_date(unix_time)
        status_message = ' has disconnected.'
        leave_room(room)
        # TODO
        # Check ZMQ buffer for newer messages
        # that have not been emitted
        zmq_buffer = next(c.next_message())
    
        if zmq_buffer:
            zmq_timestamp = zmq_buffer["timestamp"]

            if zmq_timestamp < unix_time:
                emit("message", {"msg": message["data"]}, room=message["room"], namespace="/chat")    

        while True:
            payload = next(c.next_message())
            if payload:
                payload = payload.split('|')
                message = json.loads(decrypt(payload[0], c.secret))
                digest = decrypt(payload[1], c.secret)
                if verify(json.dumps(message), digest) and message["timestamp"] < unix_time:
                    new_message = "%s: %s: %s" % (ts_to_date(message["timestamp"]), message["username"], message["message"])
                    emit("message", {"msg": new_message}, room=message["room"])
                else:
                    break
            else:
                break  
        # TODO
        # Synchronise messages here
        json_string = {
            'username': username,
            'timestamp': unix_time,
            'message': status_message,
            'room': room,
        }
        encrypted_json = encrypt(json.dumps(json_string), c.secret)
        encrypted_digest = encrypt(sha1(json.dumps(json_string)), c.secret)
        c.zmq.publish(encrypted_json + "|" + encrypted_digest)
        
        #Insert data to local database
        db.insert_message(user=username, ts=unix_time, message=status_message, room=room)

        emit('status', {'msg': datetime + ": " + username + status_message}, room=room)

@socketio.on('connect', namespace='/chat')
def test_connect():
    global thread

    if not thread:
        thread = socketio.start_background_task(target=background_thread)
        #thread = Thread(target=background_thread)
        #thread.start()

    emit('my_response', {'data': 'Connected', 'count': 0})
