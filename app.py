import os
import json
from flask import Flask, render_template, request, jsonify
from datetime import datetime
from google import genai
from google.genai import types

# --- Flask and Gemini Configuration ---

# Initialize the Flask application, setting up the path for static files (CSS, JS)
app = Flask(__name__, static_folder='static', static_url_path='/static')

# Initialize the Gemini client. 
# This process automatically searches the environment variables (specifically GEMINI_API_KEY) 
# for the API key, which is the secure, recommended method.
try:
    # Client initialization reads the key securely from the system environment.
    # The hardcoded key has been removed to maintain security best practices.
    client = genai.Client(api_key='AIzaSyDd2K0Jwjs6X_c3JyGz6Q87ZQpcschQNSo')
    print("Gemini Client Initialized Successfully.")
except Exception as e:
    # If initialization fails (e.g., API key is missing or invalid), the error is logged, 
    # and the 'client' variable is set to None to prevent API calls.
    print(f"Error initializing Gemini client: {e}. Check your GEMINI_API_KEY environment variable.")
    client = None

# Route definition for serving static files located in the 'node_modules' directory.
# This is often used for front-end libraries like Bootstrap or jQuery.
@app.route('/node_modules/<path:filename>')
def node_modules(filename):
    return app.send_static_file(f'../node_modules/{filename}') 


# Main route for the application. Handles the initial page load.
@app.route('/', methods=['GET'])
def index():
    now = datetime.now()
    # Renders the 'index.html' template file, which contains the user form and calendar, 
    # ensuring the Flask application loads the correct file.
    return render_template('index.html', date=now) 


# -------------------------------------------------------------------
# CORE ACTIVITY FINDER LOGIC
# This route handles the POST request sent from the frontend JavaScript when the user submits the form.
@app.route('/get_recommendation', methods=['POST']) 
def get_recommendation():
    # 1. Initial Checks
    # If the client failed to initialize at startup, return a 500 server error immediately.
    if not client:
        return jsonify({"recommendation": "Error: AI client not initialized. Check API Key configuration."}), 500
    # Ensure the request data is in the expected JSON format.
    if not request.is_json:
        return jsonify({"recommendation": "Missing JSON in request"}), 400

    # The entire core logic is wrapped in a try/except block to handle API communication failures
    # and invalid JSON parsing, ensuring the server doesn't crash.
    try:
        # 2. Extract and Prepare User Data
        data = request.get_json()
        location = data.get('location', 'an undisclosed location')
        budget = data.get('budget', 'flexible budget')
        # Interests are extracted from the list provided by the frontend.
        interests = data.get('interests', ['general activities'])[0] 
        availability = data.get('availability', [])

        # Format the collected calendar availability into a descriptive string for the AI prompt.
        availability_text = "Available time slots:\n"
        if availability:
            availability_text += "\n".join([f"- {slot['day']} at {slot['time']}" for slot in availability])
        else:
            availability_text += "- No specific slots provided. Suggest an activity that fits general times."

        # --- 3. Gemini System Instruction and Structured Output Schema ---
        
        # The system instruction guides the model's behavior, forcing it to act as an activity planner
        # and to strictly output three results in the required JSON format.
        system_instruction = """
        You are an expert activity and experience planner. Your task is to recommend three (3) distinct and specific activities that fit the user's profile.
        You MUST respond ONLY with a single JSON object that contains a key named 'activities', which holds an array of exactly three JSON objects, each conforming exactly to the specified schema. 
        DO NOT include any text, markdown, or explanations outside the JSON object.
        """
        
        # Define the schema for a single activity object. This structure guarantees the output 
        # includes only the required fields: name, address, cost, and a brief description.
        activity_schema = types.Schema(
            type=types.Type.OBJECT,
            properties={
                "activity_name": types.Schema(type=types.Type.STRING, description="The specific, bold title for the recommended activity/venue."),
                "address": types.Schema(type=types.Type.STRING, description="The location or address of the activity."),
                "cost_estimate": types.Schema(type=types.Type.STRING, description="A clear cost estimate that respects the user's max budget."),
                "brief_description": types.Schema(type=types.Type.STRING, description="A single, very brief sentence summarizing the activity."),
            },
            required=["activity_name", "address", "cost_estimate", "brief_description"]
        )

        # Define the overall response schema. This outer structure tells the model the final output 
        # must be an object containing the list of activities.
        response_schema = types.Schema(
            type=types.Type.OBJECT,
            properties={
                "activities": types.Schema(
                    type=types.Type.ARRAY,
                    description="A list of three distinct activity recommendations.",
                    items=activity_schema
                ),
            },
            required=["activities"]
        )

        # --- 4. User Prompt Assembly ---
        user_prompt = f"""
        **User Profile for Activity Recommendation:**
        - Location: {location}
        - Max Budget: ${budget}
        - Interests: {interests}
        
        {availability_text}

        Generate three highly relevant activity recommendation in the required JSON format.
        """

        # --- 5. Gemini API Call ---
        # Configure the request to force JSON output using the defined schema.
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json", 
            response_schema=response_schema,
        )
        
        # Send the prompt and configuration to the Gemini model.
        response = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=user_prompt,
            config=config,
        )

        # 6. Process Gemini's JSON Response
        # Parse the JSON string received from the AI into a Python dictionary.
        ai_data = json.loads(response.text)
        formatted_recommendation = ""
        recommendation_list = ai_data.get('activities', [])

        # Loop through the list of three activities and format the data into HTML for display.
        if recommendation_list:
            # Add a separator element before the list begins.
            formatted_recommendation += "<h4></h4>" 
            for i, activity in enumerate(recommendation_list):
                # Format: Bold Title (h5), Cost/Address line (p.text-muted), Brief Description (p).
                activity_html = f"""
                    <h5 class='mt-3 mb-0 text-primary'><strong>{i+1}. {activity.get('activity_name', 'No Name')}</strong></h5>
                    <p class='text-muted mb-1'>Cost: {activity.get('cost_estimate', 'N/A')} &bull; Address: {activity.get('address', 'N/A')}</p>
                    <p>{activity.get('brief_description', 'No description.')}</p>
                """
                formatted_recommendation += activity_html
        else:
            formatted_recommendation = "Could not generate activities based on the criteria. Check the raw response."

        # 7. Send the final formatted HTML back to the client.
        return jsonify({"recommendation": formatted_recommendation})

    # --- Specific Error Handling ---
    except json.JSONDecodeError:
        # Handle failures if the model returns malformed JSON despite the schema constraint.
        return jsonify({"recommendation": f"⚠️ **Error:** AI failed to produce valid JSON. Raw output: {response.text[:100]}..."}), 500
    except Exception as e:
        # Catch any other unexpected server issues (e.g., API request timeout).
        print(f"An unexpected server error occurred: {e}")
        return jsonify({"recommendation": f"❌ **Unexpected Server Error:** {str(e)}"}), 500
# -------------------------------------------------------------------

# Run the Flask app only when the script is executed directly.
if __name__ == '__main__':
    # Running on port 8080. This explicit port definition helps avoid common 
    # port 5000 conflicts experienced on some systems.
    app.run(debug=True, port=8080)