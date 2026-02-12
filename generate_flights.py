import json
import random
from datetime import datetime, timedelta
from math import cos, sin, sqrt, atan2, radians, degrees

# Major European airports with coordinates (lon, lat)
AIRPORTS = {
    'LHR': {'name': 'London Heathrow', 'coords': [-0.4543, 51.47]},
    'CDG': {'name': 'Paris Charles de Gaulle', 'coords': [2.5479, 49.0097]},
    'FRA': {'name': 'Frankfurt am Main', 'coords': [8.5622, 50.0379]},
    'AMS': {'name': 'Amsterdam Schiphol', 'coords': [4.7683, 52.3105]},
    'MAD': {'name': 'Madrid Barajas', 'coords': [-3.568, 40.4839]},
    'FCO': {'name': 'Rome Fiumicino', 'coords': [12.2389, 41.8003]},
    'MUC': {'name': 'Munich', 'coords': [11.7861, 48.3538]},
    'ZRH': {'name': 'Zurich', 'coords': [8.5492, 47.4647]},
    'VIE': {'name': 'Vienna', 'coords': [16.5697, 48.1103]},
    'DUB': {'name': 'Dublin', 'coords': [-6.2701, 53.4264]},
    'BRU': {'name': 'Brussels', 'coords': [4.4844, 50.9014]},
    'LIS': {'name': 'Lisbon', 'coords': [-9.1342, 38.7742]},
    'ATH': {'name': 'Athens', 'coords': [23.9445, 37.9364]},
    'IST': {'name': 'Istanbul', 'coords': [28.8146, 41.2619]},
    'VCE': {'name': 'Venice', 'coords': [12.3186, 45.5050]},
    'BCN': {'name': 'Barcelona', 'coords': [2.0785, 41.2971]},
    'CDT': {'name': 'Copenhagen', 'coords': [12.65, 55.618]},
    'OSL': {'name': 'Oslo', 'coords': [11.1004, 60.1939]},
    'ARN': {'name': 'Stockholm Arlanda', 'coords': [17.9186, 59.6519]},
    'WAW': {'name': 'Warsaw', 'coords': [20.9671, 52.1657]},
}

AIRLINES = ['BA', 'LH', 'AF', 'KL', 'IB', 'AZ', 'OS', 'SK', 'SN', 'RJ', 'TP', 'AA', 'UA', 'DL', 'AF']
AIRCRAFT = ['Boeing 777', 'Airbus A380', 'Airbus A320', 'Boeing 737', 'Airbus A350', 'Embraer E190']

def generate_flight_path(start_coords, end_coords, num_points=20):
    """Generate a realistic flight path with waypoints"""
    path = []
    lon1, lat1 = start_coords
    lon2, lat2 = end_coords
    
    # Calculate distance and bearing
    dLat = radians(lat2 - lat1)
    dLon = radians(lon2 - lon1)
    
    for i in range(num_points):
        t = i / (num_points - 1)
        # Linear interpolation for simplicity
        lat = lat1 + (lat2 - lat1) * t
        lon = lon1 + (lon2 - lon1) * t
        
        # Add slight altitude variation (in meters, as 3rd coordinate)
        altitude = 10000 + 3000 * sin(t * 3.14159)  # Climb then descend
        path.append([lon, lat, int(altitude)])
    
    return path

def generate_flights_for_day(date_str='2024-01-15'):
    """Generate flights for a single day"""
    base_date = datetime.strptime(date_str, '%Y-%m-%d')
    features = []
    flight_counter = 1
    
    airport_list = list(AIRPORTS.keys())
    num_flights = 350  # Realistic number for a day across Europe
    
    for _ in range(num_flights):
        # Random origin and destination
        origin_code = random.choice(airport_list)
        destination_code = random.choice([a for a in airport_list if a != origin_code])
        
        origin = AIRPORTS[origin_code]
        destination = AIRPORTS[destination_code]
        
        # Random time during the day (05:00 - 23:00)
        hour = random.randint(5, 23)
        minute = random.randint(0, 59)
        start_time = base_date.replace(hour=hour, minute=minute)
        
        # Flight duration depends on distance (roughly)
        dist = sqrt((destination['coords'][0] - origin['coords'][0])**2 + 
                   (destination['coords'][1] - origin['coords'][1])**2)
        duration_hours = 1 + (dist / 5)  # Roughly 1-5 hours
        duration_minutes = int(duration_hours * 60)
        
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        # Skip if flight ends next day
        if end_time.day != start_time.day:
            continue
        
        airline = random.choice(AIRLINES)
        flight_number = f"{airline}{random.randint(100, 9999)}"
        aircraft = random.choice(AIRCRAFT)
        
        # Generate flight path
        path = generate_flight_path(origin['coords'], destination['coords'], num_points=15)
        
        feature = {
            'type': 'Feature',
            'geometry': {
                'type': 'LineString',
                'coordinates': path
            },
            'properties': {
                'flightNumber': flight_number,
                'airline': airline,
                'aircraft': aircraft,
                'registration': f"N{random.randint(10000, 99999)}",
                'origin': origin_code,
                'originName': origin['name'],
                'destination': destination_code,
                'destinationName': destination['name'],
                'startTime': int(start_time.timestamp() * 1000),  # milliseconds
                'endTime': int(end_time.timestamp() * 1000),
                'duration': duration_minutes,
                'numPoints': len(path),
                'maxAltitude': max([p[2] for p in path])
            }
        }
        
        features.append(feature)
        flight_counter += 1
    
    return {
        'type': 'FeatureCollection',
        'features': features
    }

if __name__ == '__main__':
    # Generate realistic flight data
    geojson_data = generate_flights_for_day('2024-01-15')
    
    # Save to file
    output_path = 'dataset/airplane_flights_1day.geojson'
    with open(output_path, 'w') as f:
        json.dump(geojson_data, f)
    
    print(f"Generated {len(geojson_data['features'])} flights")
    print(f"Saved to {output_path}")
    
    # Print sample flight
    if geojson_data['features']:
        sample = geojson_data['features'][0]
        print(f"\nSample flight:")
        print(f"  {sample['properties']['flightNumber']}: {sample['properties']['originName']} → {sample['properties']['destinationName']}")
        print(f"  Time: {datetime.fromtimestamp(sample['properties']['startTime']/1000)} - {datetime.fromtimestamp(sample['properties']['endTime']/1000)}")
