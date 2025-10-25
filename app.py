from flask import Flask, render_template
from datetime import datetime

app = Flask(__name__, static_folder='static', static_url_path='/static')

app_node_modules = Flask(__name__, static_folder='node_modules', static_url_path='/node_modules')

app.add_url_rule('/node_modules/<path:filename>', endpoint='node_modules', view_func=app_node_modules.send_static_file)


@app.route('/', methods=['GET'])
def index():
    
    now = datetime.now()
    
    return render_template('index.html', date=now)

if __name__ == '__main__':
    app.run(debug=True)