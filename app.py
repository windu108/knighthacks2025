import os
import json
from flask import Flask, render_template, request, jsonify
from datetime import datetime
from google import genai
from google.genai import types

# --- Configuration ---
app = Flask(__name__, static_folder='static', static_url_path='/static')

# Initialize the Gemini client. It automatically looks for the GEMINI_API_KEY
# environment variable.
try:
    #gemini api key
    client = genai.Client(api_key='AIzaSyDd2K0Jwjs6X_c3JyGz6Q87ZQpcschQNSo')
    print("Gemini Client Initialized Successfully.")
except Exception as e:
    print(f"Error initializing Gemini client: {e}. Check your GEMINI_API_KEY environment variable.")
    client = None

# Define a view function for node_modules (can be left as is, but often unnecessary)
@app.route('/node_modules/<path:filename>')
def node_modules(filename):
    return app.send_static_file(f'../node_modules/{filename}') 


@app.route('/', methods=['GET'])
def index():
    now = datetime.now()
    return render_template('base.html', date=now) 


# -------------------------------------------------------------------
# !!! CORE ACTIVITY FINDER LOGIC !!!
@app.route('/get_recommendation', methods=['POST']) 
def get_recommendation():
    if not client:
        return jsonify({"recommendation": "Error: AI client not initialized. Check API Key configuration."}), 500

    if not request.is_json:
        return jsonify({"recommendation": "Missing JSON in request"}), 400

    try:
        data = request.get_json()
        location = data.get('location', 'an undisclosed location')
        budget = data.get('budget', 'flexible budget')
        interests = data.get('interests', ['general activities'])[0] 
        availability = data.get('availability', [])

        # Format the availability data for the prompt
        availability_text = "Available time slots:\n"
        if availability:
            availability_text += "\n".join([f"- {slot['day']} at {slot['time']}" for slot in availability])
        else:
            availability_text += "- No specific slots provided. Suggest an activity that fits general times."

        # --- 1. System Instruction & JSON Schema ---
        system_instruction = """
        You are an expert activity and experience planner. Your task is to recommend three (3) distinct and specific activities that fit the user's profile.
        You MUST respond ONLY with a single JSON object that contains a key named 'activities', which holds an array of exactly three JSON objects, each conforming exactly to the specified schema. 
        DO NOT include any text, markdown, or explanations outside the JSON object.
        """
        
        # Define the schema for a single activity object
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

        # ✅ FIX 3: Define the overall response schema to contain the 'activities' array
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

        # --- 2. User Prompt ---
        user_prompt = f"""
        **User Profile for Activity Recommendation:**
        - Location: {location}
        - Max Budget: ${budget}
        - Interests: {interests}
        
        {availability_text}

        Generate three highly relevant activity recommendation in the required JSON format.
        """

        # --- 3. Gemini API Call ---
        config = types.GenerateContentConfig(
            system_instruction=system_instruction,
            response_mime_type="application/json", 
            response_schema=response_schema,
        )
        
        response = client.models.generate_content(
            model='gemini-2.5-flash', 
            contents=user_prompt,
            config=config,
        )

        # 4. Parse the JSON output from Gemini's response text
        ai_data = json.loads(response.text)

        # Initialize the formatted HTML string
        formatted_recommendation = ""
        recommendation_list = ai_data.get('activities', [])

        # 5. Loop through the three activities and format the data into HTML
        if recommendation_list:
            # We use an empty h4 element to separate the summary from the recommendation section
            formatted_recommendation += "<h4></h4>"
            for i, activity in enumerate(recommendation_list):
                # Format the activity details as requested: Bold Title, Cost/Address, Brief Description
                # Note: We now use 'brief_description' (from the new schema) instead of 'description' (from the old schema)
                activity_html = f"""
                    <h5 class='mt-3 mb-0 text-primary'><strong>{i+1}. {activity.get('activity_name', 'No Name')}</strong></h5>
                    <p class='text-muted mb-1'>Cost: {activity.get('cost_estimate', 'N/A')} &bull; Address: {activity.get('address', 'N/A')}</p>
                    <p>{activity.get('brief_description', 'No description.')}</p>
                """
                formatted_recommendation += activity_html
        else:
            formatted_recommendation = "Could not generate activities based on the criteria. Check the raw response."

        # 6. Send the formatted HTML back to the client
        return jsonify({"recommendation": formatted_recommendation})

    except json.JSONDecodeError:
        # Handle cases where the model fails to produce valid JSON
        return jsonify({"recommendation": f"⚠️ **Error:** AI failed to produce valid JSON. Raw output: {response.text[:100]}..."}), 500
    except Exception as e:
        print(f"An unexpected server error occurred: {e}")
        return jsonify({"recommendation": f"❌ **Unexpected Server Error:** {str(e)}"}), 500
# -------------------------------------------------------------------

if __name__ == '__main__':
    app.run(debug=True, port=8080)