# API Key: AIzaSyDd2K0Jwjs6X_c3JyGz6Q87ZQpcschQNSo

from google import genai
#from google.genai import types


#Selup client using google api key
client = genai.Client(api_key='AIzaSyDd2K0Jwjs6X_c3JyGz6Q87ZQpcschQNSo')

from google import genai


response = client.models.generate_content(
    model='gemini-2.5-flash', contents='Explain some fun things to do in Orlando'
)

print(response.text)
