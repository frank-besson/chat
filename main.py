import os
import names
from flask import Flask, render_template, session, url_for, redirect, request, make_response
from flask_socketio import emit, join_room, leave_room
from flask_socketio import SocketIO
from flask_wtf import FlaskForm
from wtforms.fields import StringField, SubmitField
from wtforms.validators import DataRequired

socketioEvent = SocketIO()

target = '/chat'

class LoginForm(FlaskForm):
    """Accepts a nickname and a room."""
    name = StringField('Name', validators=[DataRequired()])
    room = StringField('Room', validators=[DataRequired()])
    submit = SubmitField('Enter Chatroom')

@socketioEvent.on('joined', namespace=target)
def joined(message):
    """Sent by clients when they enter a room.
    A status message is broadcast to all people in the room."""
    room = session.get('room')
    join_room(room)
    emit('status', {'msg': session.get('name') + ' has entered ' + session.get('room'), 'namespace':target}, room=room)

@socketioEvent.on('text', namespace=target)
def text(message):
    """Sent by a client when the user entered a new message.
    The message is sent to all people in the room."""
    room = session.get('room')
    emit('message', {'msg': session.get('name') + ': ' + message['msg'], 'namespace':target}, room=room)

@socketioEvent.on('left', namespace=target)
def left(message):
    """Sent by clients when they leave a room.
    A status message is broadcast to all people in the room"""
    room = session.get('room')
    leave_room(room)
    emit('status', {'msg': session.get('name') + ' has left the room', 'namespace':target}, room=room)

class DevelopmentConfig():
	SECRET_KEY  = 'x-yNA`mr#=/?RT0`^?9n);D[#~BR7C;9kd2iY^">zC,Z|_%E1{<!;[en4Op${e'
	PORT        = int(os.environ.get('PORT', 33507))
	DEBUG 	    = True
	DEVELOPMENT = True

def create_app():
    """Create an application."""
    app = Flask(__name__)
    app.debug = False
    app.config.from_object(DevelopmentConfig())
    socketioEvent.init_app(app)
    return app

app = create_app()

@app.context_processor
def override_url_for():
	return dict(url_for=dated_url_for)

# http://flask.pocoo.org/snippets/40/
def dated_url_for(endpoint, **values):
	if endpoint == 'static':
		filename = values.get('filename', None)
		if filename:
			file_path = os.path.join(app.root_path, endpoint, filename)
			values['q'] = int(os.stat(file_path).st_mtime)
	return url_for(endpoint, **values)

@app.route("/")
def index():
	return redirect(url_for('chat',room='General'))

@app.route('/join', methods=['GET', 'POST'])
def join():
	form = LoginForm()
	if form.validate_on_submit():
		session['name'] = form.name.data
		session['room'] = form.room.data
		#res = make_response(redirect(url_for('chat', room=session['room'], session=session['name'])))
		return redirect(url_for('chat', room=session['room']))
		#return res
	elif request.method == 'GET':
		form.name.data = session.get('name', '')
		form.room.data = session.get('room', '')
		return render_template('join.html', form=form)

@app.route("/<string:room>",  methods=['GET', 'POST'])
def chat(room='General'):
	try:
		session['name'] = session['name']
	except:
		session['name'] = names.get_full_name()
	session['room'] = room.upper()
	return render_template('index.html', room=session['room'], namespace=target)

@app.route("/about")
def about():
	return render_template('about.html')

if __name__ == "__main__":
    socketioEvent.run(app, host='0.0.0.0', port=app.config['PORT'])