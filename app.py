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
    #Create client based on the api key
    client = genai.Client(api_key='AIzaSyDd2K0Jwjs6X_c3JyGz6Q87ZQpcschQNSo')

    print("Gemini Client Initialized Successfully.")
except Exception as e:
    #Error if can't find api key
    print(f"Error initializing Gemini client: {e}. Check your GEMINI_API_KEY environment variable.")
    client = None

# Define a view function for node_modules (can be left as is, but often unnecessary)
@app.route('/node_modules/<path:filename>')
def node_modules(filename):
    return app.send_static_file(f'../node_modules/{filename}') 


@app.route('/', methods=['GET'])
def index():
    now = datetime.now()
    # Assuming index.html is actually base.html or a file that includes the form
    return render_template('base.html', date=now) 


# -------------------------------------------------------------------
# !!! CORE ACTIVITY FINDER LOGIC !!!
#Reverted route to /get_recommendation to match base.html fetch call.
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
        # interests is an array containing a single string of comma-separated interests
        # This is correct based on your frontend logic
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
        You are an expert activity and experience planner. Your task is to recommend a single, 
        specific activity that perfectly matches the user's profile. 
        You MUST respond ONLY with a single JSON object that conforms exactly to the specified schema. 
        DO NOT include any text, markdown, or explanations outside the JSON object.
        """
        
        # Define the JSON Schema the model must adhere to.
        response_schema = types.Schema(
            type=types.Type.OBJECT,
            properties={
                "activity_name": types.Schema(type=types.Type.STRING, description="The specific name of the recommended activity/venue."),
                "description": types.Schema(type=types.Type.STRING, description="A detailed, engaging description of the activity and why it fits the user's interests, location, and budget."),
                "cost_estimate": types.Schema(type=types.Type.STRING, description="A clear cost estimate (e.g., '$20-30 per person', 'Free', or 'High-End'). Must respect the user's max budget."),
                "best_time_slot_suggestion": types.Schema(type=types.Type.STRING, description="Suggest one specific, plausible time slot from the user's available times, or a general time if no slots were provided (e.g., 'Suggest Monday at 7:00 PM', or 'Any weekday evening')."),
                "fit_score": types.Schema(type=types.Type.INTEGER, description="A confidence score from 1 to 100 for how well this activity fits ALL the user criteria."),
            },
            required=["activity_name", "description", "cost_estimate", "best_time_slot_suggestion", "fit_score"]
        )

        # --- 2. User Prompt ---
        user_prompt = f"""
        **User Profile for Activity Recommendation:**
        - Location: {location}
        - Max Budget: ${budget}
        - Interests: {interests}
        
        {availability_text}

        Generate one highly relevant activity recommendation in the required JSON format.
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
        
        # 5. Format the JSON data into HTML for the frontend
        formatted_recommendation = f"""
            <h4 class='text-primary'>🎉 **{ai_data.get('activity_name', 'No Name')}**</h4>
            <p><strong>Cost Estimate:</strong> {ai_data.get('cost_estimate', 'N/A')}</p>
            <p><strong>Suggested Slot:</strong> {ai_data.get('best_time_slot_suggestion', 'N/A')}</p>
            <p class='mt-3'>{ai_data.get('description', 'No description.')}</p>
            <p class='text-success mt-3'>**Fit Score:** **{ai_data.get('fit_score', 'N/A')}/100**</p>
        """

        # 6. Send the formatted HTML back to the client
        return jsonify({"recommendation": formatted_recommendation})

    except json.JSONDecodeError:
        # Handle cases where the model fails to produce valid JSON
        return jsonify({"recommendation": f"⚠️ **Error:** AI failed to produce valid JSON. Raw output: {response.text[:100]}..."}), 500
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return jsonify({"recommendation": f"❌ **Unexpected Server Error:** {str(e)}"}), 500
# -------------------------------------------------------------------

if __name__ == '__main__':
    app.run(debug=True)