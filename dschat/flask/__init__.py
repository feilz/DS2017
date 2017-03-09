from app import create_app, socketio

app = create_app(debug=True)

#socketio.run(app, host='0.0.0.0',debug=True)