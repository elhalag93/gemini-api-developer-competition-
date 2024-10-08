from flask import Flask, request, render_template, redirect, url_for
import requests
import json
from datetime import datetime
import google.generativeai as genai
import os

# Configure the Gemini API
genai.configure(api_key='AIzaSyCQ0064nd3gWZs0AwQQ8YlHramx7ANWlKA')

# Initialize Flask application
app = Flask(__name__)

# Define the path to save uploaded images
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Function to get location
def get_location():
    try:
        response = requests.get('http://ip-api.com/json/')
        response.raise_for_status()
        data = response.json()
        
        if data['status'] == 'fail':
            return None, f"Error from the API: {data.get('message', 'Unknown error')}"
        else:
            location_data = {
                'latitude': data['lat'],
                'longitude': data['lon'],
                'city': data.get('city', 'N/A'),
                'region': data.get('regionName', 'N/A'),
                'country': data.get('country', 'N/A'),
                'zip': data.get('zip', 'N/A')
            }
            return location_data, None
    except requests.RequestException as e:
        return None, f"HTTP Request failed: {e}"
    except ValueError as e:
        return None, f"Error parsing JSON: {e}"

# Function to get the current season
def get_season(date):
    year = date.year
    seasons = {
        'Winter': (datetime(year, 12, 21).date(), datetime(year + 1, 3, 20).date()),
        'Spring': (datetime(year, 3, 21).date(), datetime(year, 6, 20).date()),
        'Summer': (datetime(year, 6, 21).date(), datetime(year, 9, 22).date()),
        'Fall': (datetime(year, 9, 23).date(), datetime(year, 12, 20).date())
    }
    for season, (start_date, end_date) in seasons.items():
        if start_date <= date <= end_date:
            return season
    return None

@app.route('/')
def upload_form():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file:
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(file_path)

        # Get location data
        location, error = get_location()
        if error:
            return f"Error getting location: {error}"

        location.pop('zip', None)

        # Get the current date and season
        current_date = datetime.now().date()
        current_season = get_season(current_date)

        # Classify the soil type using the Gemini API
        image_model = genai.GenerativeModel('gemini-1.5-flash')
        cookie_picture = {
            'mime_type': 'image/jpg',
            'data': open(file_path, 'rb').read()
        }
        prompt = '''what is the kind of this soil ? 
        i need the basic type based on the picture you have , give one or two words as response to describe the soil in picture 
        , take care the images will be taken from camera or any other source and be not good at all and hard to identify .
        even this response in max two words to identify the soil'''

        response = image_model.generate_content(contents=[prompt, cookie_picture])
        candidates = response.candidates
        if candidates:
            content = candidates[0].content
            text_parts = content.parts
            if text_parts:
                soil_type = text_parts[0].text.strip()
            else:
                soil_type = "Unknown"
        else:
            soil_type = "Unknown"

        # Generate plant recommendations
        text_model = genai.GenerativeModel('gemini-1.0-pro-latest')
        prompt = f'''I am a plant scientist working with the United Nations to develop a recommendation 
        tool to help people around the world grow plants to mitigate global warming. 
        Our mission is to recommend the best plants to grow based on location, current date, and soil type. 
        For example, recommend for someone who has {soil_type} soil in {location['city']}, {location['region']}, {location['country']} on {current_date} 
        during {current_season}. Recommend plants that can help solve global warming with the highest carbon absorption rates per tree per year.
        very important only reply with json format with recommnded plants  each plant have fields  the plant's name, scientific name and carbon absorption rate as strings with units.''' 

        response = text_model.generate_content(contents=[prompt])
        candidates = response.candidates
        recommended_plants = []
        if candidates:
            content = candidates[0].content
            text_parts = content.parts
            if text_parts:
                content_text = text_parts[0].text.strip()
                if content_text.startswith('```json'):
                    content_text = content_text[7:].strip()
                if content_text.endswith('```'):
                    content_text = content_text[:-3].strip()
                try:
                    print(f"Raw content from API: {content_text}")
                    content_dict = json.loads(content_text)
                    #recommendations = content_dict.get('recommendations', [])
                    # Ensure carbon_absorption_rate is a string
                    for plant in content_dict:
                        if isinstance(plant.get('carbon_absorption_rate'), (int, float)):
                            plant['carbon_absorption_rate'] = f"{plant['carbon_absorption_rate']} metric tons per hectare per year"
                    recommended_plants = content_dict
                    print(f"Parsed recommended plants: {recommended_plants}")
                except json.JSONDecodeError as e:
                    print(f"JSON Decode Error: {e}")
                    upload_file()
                    #return f"JSON Decode Error: {e}"

        return render_template('results.html', location=location, current_date=current_date, current_season=current_season, soil_type=soil_type, recommended_plants=recommended_plants)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)

