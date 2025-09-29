from flask import Flask, render_template, request, jsonify
from flask_cors import CORS
import pandas as pd

app = Flask(__name__)
CORS(app)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/search-buses', methods=['POST'])
def search_buses():
    try:
        data = request.get_json()
        from_station = data.get('from')
        to_station = data.get('to')
        bus_type = data.get('type')
        
        # Read bus data
        bus_data = pd.read_csv('bus_data.csv')
        
        # Filter buses based on route and type
        filtered_buses = bus_data.loc[
            (bus_data['From'] == from_station) & 
            (bus_data['To'] == to_station) & 
            (bus_data['Type'] == bus_type)
        ]
        
        if len(filtered_buses) > 0:
            # Convert to list of dictionaries
            buses_list = filtered_buses[['Route No.', 'From', 'To', 'Type', 'Fare']].to_dict('records')
            
            return jsonify({
                'status': 'success',
                'message': f'Found {len(buses_list)} bus(es)',
                'buses': buses_list
            }), 200
        else:
            return jsonify({
                'status': 'error',
                'message': f'No buses available from {from_station} to {to_station}',
                'buses': []
            }), 200
            
    except Exception as e:
        print(f"Error: {str(e)}")
        return jsonify({
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }), 500


@app.route('/submit-booking', methods=['POST'])
def submit_booking():
    try:
        data = request.get_json()
        
        from_station = data.get('from')
        to_station = data.get('to')
        date = data.get('date')
        bus_type = data.get('busType')
        route_no = data.get('routeNo')
        passengers = data.get('passengers', [])
        
        # Read bus data to get fare
        bus_data = pd.read_csv('bus_data.csv')
        
        # Get the selected bus details
        selected_bus = bus_data.loc[
            (bus_data['Route No.'] == route_no) &
            (bus_data['From'] == from_station) & 
            (bus_data['To'] == to_station)
        ]
        
        if len(selected_bus) == 0:
            return jsonify({
                'status': 'error',
                'message': 'Bus not found'
            }), 400
        
        base_fare = float(selected_bus.iloc[0]['Fare'])
        
        # ==================== FARE CALCULATIONS ====================
        
        def calculate_fare(age, base_fare):
            """Calculate fare based on age and base fare"""
            if age < 5:
                return 0  # Children under 5 travel free
            elif age < 12:
                return base_fare * 0.5  # 50% discount for children
            elif age >= 60:
                return base_fare * 0.75  # 25% discount for seniors
            else:
                return base_fare  # Full fare for adults
        
        # Calculate fare for each passenger
        passenger_details = []
        total_fare = 0
        
        for passenger in passengers:
            fare = calculate_fare(passenger['age'], base_fare)
            total_fare += fare
            passenger_details.append({
                'name': passenger['name'],
                'age': passenger['age'],
                'fare': round(fare, 2)
            })
        
        # Apply group discount if more than 4 passengers
        discount = 0
        if len(passengers) > 4:
            discount = total_fare * 0.1  # 10% group discount
            total_fare -= discount
        
        # ==================== END CALCULATIONS ====================
        
        # Print to console
        print("=" * 50)
        print("BOOKING DETAILS")
        print("=" * 50)
        print(f"Route: {from_station} → {to_station}")
        print(f"Route No: {route_no}")
        print(f"Bus Type: {bus_type}")
        print(f"Date: {date}")
        print(f"Base Fare: ₹{base_fare}")
        print("\nPassenger Details:")
        for idx, p in enumerate(passenger_details, 1):
            print(f"  {idx}. {p['name']} (Age: {p['age']}) - Fare: ₹{p['fare']}")
        
        if discount > 0:
            print(f"\nGroup Discount (10%): -₹{round(discount, 2)}")
        
        print(f"\nTOTAL FARE: ₹{round(total_fare, 2)}")
        print("=" * 50)
        
        # Return response to frontend
        return jsonify({
            'status': 'success',
            'message': 'Booking processed successfully!',
            'route_no': route_no,
            'from': from_station,
            'to': to_station,
            'date': date,
            'bus_type': bus_type,
            'base_fare': round(base_fare, 2),
            'total_passengers': len(passengers),
            'passenger_details': passenger_details,
            'discount': round(discount, 2),
            'total_fare': round(total_fare, 2)
        }), 200
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({
            'status': 'error',
            'message': f'Server error: {str(e)}'
        }), 500


if __name__ == '__main__':
    app.run(debug=True)