import requests
import os

GS_API_KEY = os.environ.get("GREATSCHOOLS_API_KEY")

def get_school_data(address, city, state):
    url = f"https://api.greatschools.org/schools/nearby?key={GS_API_KEY}&address={address}&city={city}&state={state}"

    headers = {
        "Accept": "application/json"
    }

    response = requests.get(url, headers=headers)
    response.raise_for_status()

    data = response.json()

    # Extract relevant school information (name, rating)
    school_list = []
    for school in data.get("schools", []):
        name = school.get("name")
        rating = school.get("rating")  # Assuming there's a 'rating' field
        school_list.append({"name": name, "rating": rating})

    return school_list

# Example usage (replace with actual address and city/state)
#The API key must be stored in the environment variable `GREATSCHOOLS_API_KEY`
#This script will not run without a valid API key.
if GS_API_KEY is None:
        print("Missing API Key GREATSCHOOLS_API_KEY")
else:
        address = "1600 Amphitheatre Parkway"
        city = "Mountain View"
        state = "CA"

        school_data = get_school_data(address, city, state)

        for school in school_data:
            print(f"School Name: {school['name']}, Rating: {school['rating']}")