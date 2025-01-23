Optimized Route Planner
This project provides a user-friendly web application for optimizing routes with multiple stops using the Google Maps API. It supports round trips and one-way trips, with features like address validation, route visualization, and dynamic map updates.

Features
Route Optimization: Calculate the most efficient route for multiple stops.
Interactive Map: Visualize routes dynamically using Folium.
Address Validation: Ensure accurate input with Google Maps API.
Customizable Trips: Support for round trips and one-way trips.
Two Input Methods: Manual entry or file upload for addresses.
Prerequisites
Python 3.8+ installed on your system.
Google Cloud Platform (GCP) account with API key enabled for:
Geocoding API
Places API
Directions API
Required Python libraries:
streamlit, numpy, folium, streamlit_folium, polyline, streamlit_elements, geopy, and requests.
Setup Instructions
Clone the repository:

bash
Copy
Edit
git clone <repository-url>
cd <repository-folder>
Install dependencies:

bash
Copy
Edit
pip install -r requirements.txt
Set up Google API key:

Add your API key to st.secrets file:
plaintext
Copy
Edit
[secrets]
GOOGLE_API_KEY = "your-api-key-here"
Run the application:

bash
Copy
Edit
streamlit run app.py
