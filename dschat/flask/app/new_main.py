from flask_socketio import emit, join_room, leave_room, SocketIO
from flask import Flask, session, redirect, url_for, render_template, request, make_response

from flask_wtf import Form

from wtforms.fields import StringField, SubmitField
from wtforms.validators import Required

import os

class LoginForm(Form):
    """Accepts a nickname and a room."""
    name = StringField('Name', validators=[Required()])
    room = StringField('Room', validators=[Required()])
    submit = SubmitField('Enter Chatroom')

    
socketio = SocketIO()


# Get current working directory and join it with the location of chat templates
tmpl_dir = os.path.join(os.getcwd(), 'dschat/flask/app/templates')

app = Flask(__name__, template_folder=tmpl_dir)
app.debug = True
app.config['SECRET_KEY'] = 'this_needs_to_be_changed'

# Routes for app
@app.route('/', methods=['GET', 'POST'])
def index():
    """"Login form to enter a room."""
    form = LoginForm()
    if form.validate_on_submit():
        session['name'] = form.name.data
        session['room'] = form.room.data
        return redirect(url_for('.chat'))
    elif request.method == 'GET':
        form.name.data = session.get('name', '')
        form.room.data = session.get('room', '')
    return render_template('index.html', form=form)

@app.route('/chat')
def chat():
    """Chat room. The user's name and room must be stored in
    the session."""
    name = session.get('name', '')
    room = session.get('room', '')
    if name == '' or room == '':
        return redirect(url_for('.index'))
    response = make_response(render_template('chat.html', name=name, room=room))
    response.set_cookie('usernick', session.get('name', ''))
    return response


# Events for socketio
@socketio.on('joined', namespace='/chat')
def joined(message):
    """Sent by clients when they enter a room.
    A status message is broadcast to all people in the room."""
    room = session.get('room')
    join_room(room)
    emit('status', {'msg': session.get('name') + ' has entered the room.'}, room=room)


@socketio.on('text', namespace='/chat')
def text(message):
    """Sent by a client when the user entered a new message.
    The message is sent to all people in the room."""
    room = session.get('room')
    emit('message', {'msg': session.get('name') + ':' + message['msg']}, room=room)


@socketio.on('left', namespace='/chat')
def left(message):
    """Sent by clients when they leave a room.
    A status message is broadcast to all people in the room."""
    room = session.get('room')
    leave_room(room)
    emit('status', {'msg': session.get('name') + ' has left the room.'}, room=room)

    

socketio.init_app(app)