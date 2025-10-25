from flask import Flask, render_template,session, request
from datetime import datetime

app = Flask(__name__, static_folder='static', static_url_path='/static')

app_node_modules = Flask(__name__, static_folder='node_modules', static_url_path='/node_modules')

app.add_url_rule('/node_modules/<path:filename>', endpoint='node_modules', view_func=app_node_modules.send_static_file)


activities = []

@app.route('/', methods=['GET'])
def index():
    now = datetime.now()
    return render_template('index.html', date=now)

@app.route('/logout')
def logout():
    return "You have been logged out."

@app.route('/login', methods=['POST'])
def login():
    username = request.form['username']
    session['username'] = username
    return f"Welcome, {username}!"

@app.route('/vote/<int:activity_id>')
def vote(activity_id):
    return f"You voted for activity ID {activity_id}."

@app.route('/results')
def results():
    return "Here are the voting results."


if __name__ == '__main__':
    app.run(debug=True)