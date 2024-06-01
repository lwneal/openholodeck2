import flask

app = flask.Flask(__name__)


@app.route('/')
def index():
    return flask.send_from_directory('static', 'client.html')


# TODO: Provide the communication for clients to establish WebRTC connections


if __name__ == '__main__':
    app.run(port=8000)
