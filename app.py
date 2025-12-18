import os
import json
from flask import Flask, render_template, request, jsonify
from datetime import datetime
from google import genai
from google.genai import types

# --- Flask and Gemini Configuration ---
app = Flask(__name__, static_folder='static', static_url_path='/static')

# Initialize the Gemini client
try:
    client = genai.Client(api_key='AIzaSyDd2K0Jwjs6X_c3JyGz6Q87ZQpcschQNSo')
    print("Gemini Client Initialized Successfully.")
except Exception as e:
    print(f"Error initializing Gemini client: {e}")
    client = None

# Keep last submitted entries in memory for /results
last_entries = []
last_ai_html = None

# Route to serve node_modules if needed
@app.route('/node_modules/<path:filename>')
def node_modules(filename):
    return app.send_static_file(f'../node_modules/{filename}') 

# Main page
@app.route('/calendar', methods=['GET'])
def index():
    now = datetime.now()
    return render_template('index.html', date=now)

@app.route('/')
def login():
    now = datetime.now()
    return render_template('login.html', date=now)

# Results page: display AI recommendation for last submitted data
@app.route('/results', methods=['GET'])
def results():
    if not last_ai_html:
        return render_template('results.html', ai_recommendation="No AI recommendation submitted yet.")
    
    return render_template('results.html', ai_recommendation=last_ai_html)

# Receive data from frontend (Firebase)
@app.route('/receive-data', methods=['POST'])
def receive_data():
    global last_entries, last_ai_html
    
    data = request.get_json()
    entries = data["entries"]
    for entry in entries:
        print(entry)
    last_entries = entries  # store for /results

    # Generate AI recommendation and print it
    last_ai_html = get_recommendation(entries)
    
    return jsonify({
        "message": "Data received successfully",
        "entries_received": len(entries),
        "ai_html": last_ai_html
    })

# --- Gemini logic ---
def get_recommendation(data):
    if not client:
        print("AI client not initialized")
        return "AI client not initialized"

    if not data:
        return "No user entries provided."

    try:
        # Compute minimum budget
        min_budget = min(float(entry.get("budget", float("inf"))) for entry in data)
        print("Minimum budget:", min_budget)

        # Concatenate interests
        interests = " ".join(f"{entry.get('interests','')}" for entry in data)
        print("Interests:", interests)

        # Concatenate locations, default to Orlando if missing
        locations = ", ".join(entry.get('location', 'Orlando') for entry in data)
        print("Locations:", locations)

        # System instruction
        system_instruction = """
        You are an expert activity and experience planner. Recommend 3 distinct activities
        for multiple users. Respond ONLY with JSON object with key 'activities'.
        """

        # Activity schema
        activity_schema = types.Schema(
            type=types.Type.OBJECT,
            properties={
                "activity_name": types.Schema(type=types.Type.STRING),
                "address": types.Schema(type=types.Type.STRING),
                "cost_estimate": types.Schema(type=types.Type.STRING),
                "brief_description": types.Schema(type=types.Type.STRING),
                "website_link": types.Schema(type=types.Type.STRING)
            },
            required=["activity_name","address","cost_estimate","brief_description","website_link"]
        )

        response_schema = types.Schema(
            type=types.Type.OBJECT,
            properties={
                "activities": types.Schema(type=types.Type.ARRAY, items=activity_schema)
            },
            required=["activities"]
        )

        # User prompt
        user_prompt = f"""
        Locations: {locations}
        Max Budget: ${min_budget}
        Interests: {interests}
        """

        # Generate content
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json",
            response_schema=response_schema
        )

        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=user_prompt,
            config=config
        )

        # Print raw AI response
        print("Received AI Response:")
        print(response.text)

        # Parse JSON and build HTML
        ai_data = json.loads(response.text)
        recommendation_list = ai_data.get('activities', [])
        formatted_recommendation = ""

        for i, activity in enumerate(recommendation_list, start=1):
            print(f"{i}. {activity.get('activity_name')}")
            print(f"   Address: {activity.get('address')}")
            print(f"   Cost: {activity.get('cost_estimate')}")
            print(f"   Description: {activity.get('brief_description')}")
            print(f"   Website: {activity.get('website_link')}\n")

            formatted_recommendation += f"""
            <h5 class='mt-3 mb-0 text-primary'><strong>{i}. {activity.get('activity_name')}</strong></h5>
            <p class='text-muted mb-1'>Cost: {activity.get('cost_estimate')} &bull; Address: {activity.get('address')}</p>
            <p>{activity.get('brief_description')}</p>
            <p><a href="{activity.get('website_link')}" target="_blank" class="btn btn-sm btn-outline-secondary">Learn More</a></p>
            <hr>
            """

        return formatted_recommendation or "No activities generated"

    except Exception as e:
        print(f"Error generating recommendation: {e}")
        return f"Error generating recommendation: {e}"

# Run Flask
if __name__ == '__main__':
    app.run(debug=False, port=8080)
