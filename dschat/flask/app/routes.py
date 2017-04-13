
import os
import logging
from flask import Blueprint, session, render_template, make_response, request, url_for, redirect
from dschat.flask.app.forms.login_form import LoginForm


main = Blueprint("main", __name__, template_folder=os.path.join(os.getcwd(), "dschat/flask/app/templates"))
log = logging.getLogger("dschat")

@main.route('/', methods=['GET', 'POST'])
def index():
    """"Login form to enter a room."""
    log.info("Incoming conncetion from %s" % request.remote_addr)
    form = LoginForm()
    if form.validate_on_submit():
        session['name'] = form.name.data
        session['room'] = form.room.data
        return redirect(url_for('.chat'))
    elif request.method == 'GET':
        form.name.data = session.get('name', '')
        form.room.data = session.get('room', '')
    return render_template('index.html', form=form)

@main.route('/chat')
def chat():
    """Chat room. The user's name and room must be stored in
    the session."""
    name = session.get('name', '')
    room = session.get('room', '')
    if name == '' or room == '':
        return redirect(url_for('.index'))
    response = make_response(render_template('chat.html', name=name, room=room))
    return response
