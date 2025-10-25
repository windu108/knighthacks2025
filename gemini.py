# API Key: AIzaSyDd2K0Jwjs6X_c3JyGz6Q87ZQpcschQNSo
from google import genai

# Setup client using google api key
client = genai.Client(api_key='AIzaSyDd2K0Jwjs6X_c3JyGz6Q87ZQpcschQNSo')

# variables for input
location = "Orlando"
budget = 50
responses = []

# these are responses from all of the users
responses.append("Hiking, Skydiving, Snorkling")
responses.append("Hiking, Themeparks")
responses.append("Great Food")

# ----------------------------------------------------
# 1. Format the user responses into the desired string
# ----------------------------------------------------
formatted_responses = ""
for i, response in enumerate(responses):
    # User index starts at 1, so we use i + 1
    formatted_responses += f"User{i + 1}: ({response}) " 

# ----------------------------------------------------
# 2. Construct the final prompt string
# ----------------------------------------------------
prompt = f'We have multiple users who all reside in {location}. They have a budget of ${budget}. Their interests are as follows: {formatted_responses} Suggest a single activity that would be a good fit for all of them within the budget and location. Put your response in the following format: give the name of the activity in bold, then list its cost and address on the next line then finally a very short description of the activity. Give 3 options in order of most relevant to our users interest'

# The resulting prompt string will be:
# 'We have multiple users who all reside in Orlando. They have a budget of $50. Their interests are as follows: User1: (Hiking, Skydiving, Snorkling) User2: (Hiking, Themeparks) User3: (Great Food) Suggest a single activity that would be a good fit for all of them.'

# ----------------------------------------------------
# 3. Google Gemini API call
# ----------------------------------------------------
response = client.models.generate_content(
    model='gemini-2.5-flash', 
    contents=prompt
)

# ----------------------------------------------------
# 4. Print result
# ----------------------------------------------------
print(response.text)