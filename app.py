# app.py

# API Key: AIzaSyDd2K0Jwjs6X_c3JyGz6Q87ZQpcschQNSo
from google import genai
from flask import Flask, render_template, request, jsonify
from datetime import datetime

# Setup client using google api key
# NOTE: In a production app, you would load this from an environment variable!
client = genai.Client(api_key='AIzaSyDd2K0Jwjs6X_c3JyGz6Q87ZQpcschQNSo')

# Initialize the main Flask app
# NOTE: Ensure you have a 'templates' folder with 'index.html' and 
# a 'static' folder for assets.
app = Flask(__name__, static_folder='static', static_url_path='/static')

# ----------------------------------------------------------------------
# Helper Route for node_modules (if you are using local packages like Bootstrap)
# ----------------------------------------------------------------------
@app.route('/node_modules/<path:filename>')
def node_modules(filename):
    """
    Serves files from the 'node_modules' directory for development.
    Requires 'node_modules' to be in the same directory as this script.
    """
    return app.send_static_file(f'../node_modules/{filename}') 

# ----------------------------------------------------------------------
# Route to Serve the Main Page
# ----------------------------------------------------------------------
@app.route('/', methods=['GET'])
def index():
    """
    Renders the main page template (e.g., index.html).
    """
    now = datetime.now()
    return render_template('index.html', date=now) 

# ----------------------------------------------------------------------
# Route to Process Data and Call the Gemini API
# ----------------------------------------------------------------------
@app.route('/get_recommendation', methods=['POST'])
def get_recommendation():
    """
    Receives user data from the front-end, constructs a prompt, 
    calls the Gemini API, and returns the AI's recommendation.
    """
    if not request.is_json:
        return jsonify({"message": "Missing JSON in request"}), 400

    data = request.get_json()

    # Extract the fields from the received JSON data
    location = data.get('location', 'Unknown City')
    budget = data.get('budget', 'flexible') 
    
    # Assuming 'interests' is an array of strings like: 
    # ["Hiking, Skydiving, Snorkling", "Hiking, Themeparks", "Great Food"]
    responses = data.get('interests', []) 

    # --- Fallback/Static Data for Testing if dynamic data is missing ---
    if not responses:
         responses = ["Hiking, Skydiving, Snorkling", "Hiking, Themeparks", "Great Food"]

    # 1. Format the user responses into the desired string (User1: (response) User2: (response) ...)
    formatted_responses = ""
    for i, response in enumerate(responses):
        formatted_responses += f"User{i + 1}: ({response}) " 

    # 2. Construct the final prompt string with detailed instructions
    prompt = (
        f'We have multiple users who all reside in {location}. They have a budget of ${budget}. '
        f'Their interests are as follows: {formatted_responses} '
        'Suggest a single activity that would be a good fit for all of them within the budget and location. '
        'Put your response in the following format: give the name of the activity in bold, then list its cost and address on the next line then finally a very short description of the activity. '
        'Give 3 options in order of most relevant to our users interest'
    )
    
    # 3. Google Gemini API call
    try:
        gemini_response = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=prompt
        )
        result_text = gemini_response.text
    except Exception as e:
        print(f"Gemini API Error: {e}")
        # Return a clean error message to the user
        result_text = "Sorry, the recommendation service ran into an error."

    # 4. Return the result back to the client-side JavaScript
    return jsonify({
        "status": "success",
        "recommendation": result_text,
        "location": location # Echo back some data for confirmation
    })

# ----------------------------------------------------------------------
# Run the Flask App
# ----------------------------------------------------------------------
if __name__ == '__main__':
    # 'debug=True' reloads the server automatically on file changes
    app.run(debug=True)