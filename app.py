from flask import Flask, render_template, request, jsonify
from datetime import datetime

# Initialize the main Flask app
app = Flask(__name__, static_folder='static', static_url_path='/static')

# Define a view function to serve files from the 'node_modules' directory
# This handles the script tags like src="{{ url_for('node_modules', filename='bootstrap/...') }}"
@app.route('/node_modules/<path:filename>')
def node_modules(filename):
    # This serves files from the 'node_modules' folder at the root level of your project
    # Ensure your 'node_modules' folder is peer-to-peer with 'app.py' and 'static'
    return app.send_static_file(f'../node_modules/{filename}') 


@app.route('/', methods=['GET'])
def index():
    """
    Renders the index.html template, which extends base.html.
    """
    now = datetime.now()
    
    # We now render 'index.html', which will pull in all content from 'base.html'
    return render_template('index.html', date=now) 


# --- THE ROUTE TO RECEIVE DATA ---
@app.route('/submit_data', methods=['POST'])
def submit_data():
    """
    Receives JSON data (Location, Budget, Availability) sent via the fetch API
    from the client-side JavaScript in base.html.
    """
    if not request.is_json:
        return jsonify({"message": "Missing JSON in request"}), 400

    data = request.get_json()

    # Extract the fields
    location = data.get('location', 'N/A')
    budget = data.get('budget', 'N/A')
    availability = data.get('availability', [])

    # --- Processing the Data in Python ---
    
    # You can print the data to your terminal for debugging:
    print("-" * 30)
    print(f"✅ Data Received at {datetime.now().strftime('%H:%M:%S')}")
    print(f"Location: {location}")
    print(f"Budget: {budget}")
    print(f"Number of available slots: {len(availability)}")
    
    # --- End of Processing ---

    # Return a JSON response back to the JavaScript
    num_slots = len(availability)
    response = {
        "status": "success",
        # This message will be displayed in the HTML output box
        "message": f"Server successfully processed your data! Found {num_slots} available slots.",
        "slots_count": num_slots
    }

    return jsonify(response)

if __name__ == '__main__':
    # Ensure all HTML files are in the 'templates' folder.
    app.run(debug=True)