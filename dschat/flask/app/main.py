
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
import logging


log = logging.getLogger("dschat")
db = Database()

app = Flask(__name__)
app.config["SECRET_KEY"] = "CHANGEME"
app.register_blueprint(main)
socketio = SocketIO(app)
thread = None

c = None


def background_thread():
    log.info("Starting background thread...")
    global c
    if not c:
        print("here")
        log.info("Initializing Connector")
        c = Connector()
        print("where")
        c.connect()
        log.info("Connector initialized")

    print("there")
    log.info("Starting background thread loop")
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
    log.info("JOINED: Socketio join detected")
    log.info("JOINED: Getting join parameters")
    room = session.get('room')
    join_room(room)
    username = session.get('name')
    unix_time = create_timestamp()
    datetime = ts_to_date(unix_time)
    status_message = ' has entered the room.'

    # TODO
    # Check ZMQ buffer for newer messages
    # that have not been emitted
    log.info("JOINED: Check ZMQ buffer for messages not yet emitted")
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
    log.info("JOINED: Checking if user already in database...")
    if not db.user_exists(username):
        log.info("JOINED: User not in database, adding user to database")
        db.insert_user(user=username)
    
    # TODO
    # Synchronise messages here
    if c:
        log.info("JOINED: Creating json string for ZMQ messaging")
        json_string = {
            'username': username,
            'timestamp': unix_time,
            'message': status_message,
            'room': room,
        }
        log.info("JOINED: Encrypting and hashing json string...")
        encrypted_json = encrypt(json.dumps(json_string), c.secret)
        encrypted_digest = encrypt(sha1(json.dumps(json_string)), c.secret)
        log.info("JOINED: Encrypting and hashing done.")
        log.info("JOINED: ZMQ publish")
        c.zmq.publish(encrypted_json + "|" + encrypted_digest)

    #Insert data to local database
    log.info("JOINED: Inserting join message to local database")
    db.insert_message(user=username, ts=unix_time, message=status_message, room=room)
    
    log.info("JOINED: Emitting join message to chat window")
    emit('status', {'msg': datetime + ": " + username + status_message}, room=room)


@socketio.on('text', namespace='/chat')
def text(message):
    """Sent by a client when the user entered a new message.
    The message is sent to all people in the room."""
    log.info("TEXT: Socketio text detected")
    log.info("TEXT: Getting text parameters")
    room = session.get('room')
    username = session.get('name')
    unix_time = create_timestamp()
    datetime = ts_to_date(unix_time)
    status_message = message['msg']
    
    # TODO
    # Check ZMQ buffer for newer messages
    # that have not been emitted
    log.info("TEXT: Check ZMQ buffer for messages not yet emitted")
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
    # Synchronise messages here
    if c:
        log.info("TEXT: Creating json string for ZMQ messaging")
        json_string = {
            'username': username,
            'timestamp': unix_time,
            'message': status_message,
            'room': room,
        }
        log.info("TEXT: Encrypting and hashing json string...")
        encrypted_json = encrypt(json.dumps(json_string), c.secret)
        encrypted_digest = encrypt(sha1(json.dumps(json_string)), c.secret)
        log.info("TEXT: Encrypting and hashing done.")
        log.info("TEXT: ZMQ publish")
        c.zmq.publish(encrypted_json + "|" + encrypted_digest)

    #Insert data to local database
    log.info("JOINED: Inserting message to local database")
    db.insert_message(user=username, ts=unix_time, message=status_message, room=room)
    
    log.info("JOINED: Emitting message to chat window")
    emit('message', {'msg': datetime + ": " + username + ':' + status_message}, room=room)


@socketio.on('left', namespace='/chat')
def left(message):
    """Sent by clients when they leave a room.
    A status message is broadcast to all people in the room."""
    log.info("LEFT: Socketio left detected")
    log.info("LEFT: Getting left parameters")
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
    log.info("JOINED: Check ZMQ buffer for messages not yet emitted")
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
    # Synchronise messages here
    if c:
        log.info("TEXT: Creating json string for ZMQ messaging")
        json_string = {
            'username': username,
            'timestamp': unix_time,
            'message': status_message,
            'room': room,
        }
        log.info("TEXT: Encrypting and hashing json string...")
        encrypted_json = encrypt(json.dumps(json_string), c.secret)
        encrypted_digest = encrypt(sha1(json.dumps(json_string)), c.secret)
        log.info("TEXT: Encrypting and hashing done.")
        log.info("TEXT: ZMQ publish")
        c.zmq.publish(encrypted_json + "|" + encrypted_digest)
    
    #Insert data to local database
    log.info("JOINED: Inserting leave message to local database")
    db.insert_message(user=username, ts=unix_time, message=status_message, room=room)

    log.info("JOINED: Emitting leave message to chat window")
    emit('status', {'msg': datetime + ": " + username + status_message}, room=room)

@socketio.on('disconnect', namespace='/chat')
def disconnected():
    """Called when client is disconnected by accident or by browser closing."""
    if session.get('left') is None:
        log.info("LEFT: Socketio disconnect detected")
        log.info("LEFT: Getting disconnect parameters")
        room = session.get('room')
        username = session.get('name')
        unix_time = create_timestamp()
        datetime = ts_to_date(unix_time)
        status_message = ' has disconnected.'
        leave_room(room)
        # TODO
        # Check ZMQ buffer for newer messages
        # that have not been emitted  
        log.info("JOINED: Check ZMQ buffer for messages not yet emitted")
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
        # Synchronise messages here
        if c:
            log.info("TEXT: Creating json string for ZMQ messaging")
            json_string = {
                'username': username,
                'timestamp': unix_time,
                'message': status_message,
                'room': room,
            }
            log.info("TEXT: Encrypting and hashing json string...")
            encrypted_json = encrypt(json.dumps(json_string), c.secret)
            encrypted_digest = encrypt(sha1(json.dumps(json_string)), c.secret)
            log.info("TEXT: Encrypting and hashing done.")
            log.info("TEXT: ZMQ publish")
            c.zmq.publish(encrypted_json + "|" + encrypted_digest)
        
        #Insert data to local database
        log.info("JOINED: Inserting disconnect message to local database")
        db.insert_message(user=username, ts=unix_time, message=status_message, room=room)

        log.info("JOINED: Emitting disconnect message to chat window")
        emit('status', {'msg': datetime + ": " + username + status_message}, room=room)

@socketio.on('connect', namespace='/chat')
def test_connect():
    global thread

    if not thread:
        thread = socketio.start_background_task(target=background_thread)
        #thread = Thread(target=background_thread)
        #thread.start()

    emit('my_response', {'data': 'Connected', 'count': 0})
