import os
from flask import (
    Flask, 
    render_template, 
    session, 
    request, 
    send_from_directory, 
    redirect, 
    url_for
)
from datetime import datetime

activities = []

app = Flask(__name__, static_folder='static', static_url_path='/static')
app.secret_key = 'your_random_secret_key_here' 

@app.route('/node_modules/<path:filename>')
def node_modules(filename):
    return send_from_directory(
        os.path.join(app.root_path, 'node_modules'), filename
    )


@app.route('/', methods=['GET'])
def index():
    now = datetime.now()
    return render_template('index2.html', date=now)

@app.route('/home')
def home():
    if 'username' not in session:
        return redirect(url_for('index'))
    
    return render_template('home.html',activities=activities)

@app.route('/login', methods=['POST'])
def login():
    session['username'] = request.form['username']
    session['voted_on'] = []
    return redirect(url_for('home'))


@app.route('/add_activity', methods=['POST'])
def add_activity():
    if 'username' not in session:
        return redirect(url_for('index'))

    activity_name = request.form.get('activity_name')
    
    if activity_name:
        if not activities:
            new_id = 1
        else:
            new_id = max(activity['id'] for activity in activities) + 1
            
        new_activity = {
            'id': new_id,
            'name': activity_name,
            'votes': 0
        }
        activities.append(new_activity)
    
    return redirect(url_for('home'))


@app.route('/logout', methods=['POST'])
def logout():
    session.pop('username', None) 
    session.pop('voted_on', None)
    return redirect(url_for('index')) 


@app.route('/vote/<int:activity_id>', methods=['POST'])
def vote(activity_id):
    if 'username' not in session:
        return redirect(url_for('index'))
    
    if activity_id in session.get('voted_on', []):
        print(f"User '{session['username']}' already voted for {activity_id}")
        return redirect(url_for('home'))
    
    for activity in activities:
        if activity['id'] == activity_id:
            activity['votes'] += 1 
            print(f"User '{session['username']}' voted for {activity['name']}")
            session.setdefault('voted_on', []).append(activity_id)
            session.modified = True
            break 
    return redirect(url_for('home'))

@app.route('/results')
def results():
    if 'username' not in session:
        return redirect(url_for('index'))
    
    sorted_activities = sorted(activities, key=lambda x: x['votes'], reverse=True)
    return render_template('results.html', activities=sorted_activities)

if __name__ == '__main__':
    app.run(debug=True)