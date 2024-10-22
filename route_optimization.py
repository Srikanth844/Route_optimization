import streamlit as st
import numpy as np
import time
from geopy.geocoders import GoogleV3
import folium
from streamlit_folium import folium_static
import requests
import polyline
from folium.plugins import BeautifyIcon
from streamlit_elements import elements, mui, html


def create_pulsing_icon():
    return BeautifyIcon(
        icon_shape='circle',
        border_color='#b3334f',
        border_width=5,
        text_color='blue',
        icon_size=(15, 15),
        inner_icon_style='opacity:0.5;background-color:#b3334f;',
        spin=True,
        border_opacity=0.7,
    )
def validate_address(address, api_key):
    base_url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {
        "address": address,
        "key": api_key
    }
    response = requests.get(base_url, params=params)
    data = response.json()
    if data['status'] == 'OK':
        return True, data['results'][0]['formatted_address']
    else:
        return False, None

def create_route_visualization(optimized_route):
    with elements("route_viz"):
        with mui.Stack(spacing=2, direction="column", alignItems="flex-start"):
            for i, address in enumerate(optimized_route):
                color = "green" if i == 0 or i == len(optimized_route) - 1 else "red"
                circle = "🟢" if color == "green" else "🔴"
                with mui.Stack(direction="row", spacing=2, alignItems="center"):
                    mui.Typography(f"{circle} Stop {i+1}: {address}")
                if i < len(optimized_route) - 1:
                    mui.Box(
                        sx={
                            "width": "2px",
                            "height": "20px",
                            "backgroundColor": "text.disabled",
                            "marginLeft": "10px",
                        }
                    )
def get_address_suggestions(api_key, input_text):
    if len(input_text) < 3:
        return []
    url = "https://maps.googleapis.com/maps/api/place/autocomplete/json"
    params = {
        "input": input_text,
        "key": api_key,
        "types": "address"
    }
    response = requests.get(url, params=params)
    data = response.json()
    if data["status"] == "OK":
        return [prediction["description"] for prediction in data["predictions"]]
    return []
def get_optimized_route(addresses, api_key, round_trip=True):
    if round_trip:
        return optimize_route_with_google(addresses, api_key, round_trip) + (None,)  # Add None for error_message
    else:
        start = addresses[0]
        possible_ends = addresses[1:]
        best_route = None
        best_distance = float('inf')
        
        for end in possible_ends:
            temp_addresses = [start] + [addr for addr in possible_ends if addr != end] + [end]
            route, order, distance, duration, polyline = optimize_route_with_google(temp_addresses, api_key, False)
            
            if route and distance < best_distance:
                best_route = (route, order, distance, duration, polyline)
                best_distance = distance
        
        return best_route + (None,)  # Add None for error_message # Add None for error_message

def optimize_route_with_google(addresses, api_key, round_trip=True):
    base_url = "https://maps.googleapis.com/maps/api/directions/json"
    origin = addresses[0]
    
    if round_trip:
        destination = origin
        waypoints = addresses[1:]  # Include all addresses except the first one
    else:
        destination = addresses[-1]
        waypoints = addresses[1:-1]
    flat_waypoints = [item for sublist in waypoints if isinstance(sublist, list) for item in sublist]
    waypoints = flat_waypoints if flat_waypoints else waypoints
    
    params = {
        "origin": origin,
        "destination": destination,
        "waypoints": "optimize:true|" + "|".join(waypoints),
        "key": api_key
    }

    response = requests.get(base_url, params=params)
    data = response.json()

    if data['status'] == 'OK':
        route = [origin]
        for leg in data['routes'][0]['legs']:
            route.append(leg['end_address'])
        
        if round_trip:
            optimized_order = [0] + [int(i)+1 for i in data['routes'][0]['waypoint_order']] + [0]
        else:
            optimized_order = [0] + [int(i)+1 for i in data['routes'][0]['waypoint_order']] + [len(addresses)-1]
        
        total_distance = sum(leg['distance']['value'] for leg in data['routes'][0]['legs']) / 1609.34
        total_duration_minutes = sum(leg['duration']['value'] for leg in data['routes'][0]['legs']) / 60
        
        total_duration_hours = int(total_duration_minutes // 60)
        total_duration_minutes_remainder = int(total_duration_minutes % 60)
        
        route_polyline = data['routes'][0]['overview_polyline']['points']
        
        return route, optimized_order, total_distance, (total_duration_hours, total_duration_minutes_remainder), route_polyline
    else:
        st.error(f"Error in API response: {data['status']}")
        return None, None, None, None, None

def main():
    st.set_page_config(layout="wide", page_title="Optimized Route Planner")
    
    st.markdown("""
    <style>
    .big-font {
        font-size: 20px !important;
        font-weight: bold;
    }
    .stApp {
        
        background-size: cover;
    }
    .stApp > header {
        background-color: transparent;
    }
    .stApp .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    .centered {
        text-align: center;
    }
    .column-gap {
        padding: 0 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<h1 class="centered">Optimized Route Planner</h1>', unsafe_allow_html=True)
    st.markdown('<p class="centered">This app helps you plan an optimized route for multiple stops.</p>', unsafe_allow_html=True)

    # Create two columns for the layout
    col1, gap, col2 = st.columns([47, 6, 47])

    with col2:
        st.markdown('<div class="column-gap">', unsafe_allow_html=True)
        st.subheader("Route Map")
        # Initialize the map
        default_location = [29.749907, -95.358421]  # New York City
        m = folium.Map(location=default_location, zoom_start=12)
        folium.Marker(default_location, popup="Default Location (Houston)").add_to(m)
        
        # Display the initial map
        map_container = st.empty()
        with map_container:
            folium_static(m)

    with col1:
        st.markdown('<div class="column-gap">', unsafe_allow_html=True)
        st.subheader("Route Details")
        
        radio_col1, radio_col2 = st.columns(2)
        with radio_col1:
            # Trip type selection
            trip_type = st.radio("Select trip type:", ("Round Trip", "One-Way Trip"))
            round_trip = trip_type == "Round Trip"

        with radio_col2:
            # Input method selection
            input_method = st.radio("Choose input method:", ("Manual Entry", "File Upload"))

        api_key = st.secrets["GOOGLE_API_KEY"]
        geolocator = GoogleV3(api_key=api_key) 
        addresses = []

        if input_method == "Manual Entry":
            num_locations = st.number_input("Number of locations (including start and end points)", min_value=2, value=2, step=1)
            for i in range(num_locations):
                address = st.text_input(f"Address for location {i+1}", key=f"address_{i}")
                if address:
                    addresses.append(address)  # Make sure this is adding a string, not a list
        else:
            uploaded_file = st.file_uploader("Choose a file", type="txt")
            if uploaded_file is not None:
                addresses = [line.decode("utf-8").strip() for line in uploaded_file]

        if st.button("Optimize Route") and addresses:
            with st.spinner("Optimizing route..."):
                optimized_route, optimized_order, total_distance, total_duration, route_polyline, error_message = get_optimized_route(addresses, api_key, round_trip)

            if error_message:
                st.error(error_message)
            elif optimized_route:
                st.markdown('<p class="big-font">Optimized Route Results:</p>', unsafe_allow_html=True)
                st.subheader(f"Optimized {'Round Trip' if round_trip else 'One-Way Trip'} Route:")

                create_route_visualization(optimized_route)
                st.write(f"Total Distance: {total_distance:.2f} miles")
                st.write(f"Total Duration: {total_duration[0]} hours {total_duration[1]} minutes")

                # Update the map in col2 (not col1)
                route_coordinates = polyline.decode(route_polyline)
                m = folium.Map(location=route_coordinates[0], zoom_start=10)
                
                for i, address in enumerate(optimized_route):
                    location = geolocator.geocode(address)
                    if location:
                        folium.Marker(
                            [location.latitude, location.longitude],
                            popup=f"Stop {i+1}: {address}",
                            icon=create_pulsing_icon()
                        ).add_to(m)
                
                folium.PolyLine(route_coordinates, color="blue", weight=2.5, opacity=0.8).add_to(m)

                # Update the map in the container
                with map_container:
                    folium_static(m, width=700, height=500)
            else:
                st.error("Failed to optimize route. Please check your addresses and try again.")
        elif not addresses:
            st.warning("Please provide at least two addresses.")

if __name__ == "__main__":
    main()