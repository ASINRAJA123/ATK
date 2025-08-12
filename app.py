from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime, time

# --- Configuration ---
MONGO_URI = "mongodb+srv://student:student@cluster0.tt1v1.mongodb.net/"
DB_NAME = "Codissia"

# --- Flask App Initialization ---
app = Flask(__name__)
CORS(app)

# --- MongoDB Connection ---
try:
    client = MongoClient(MONGO_URI)
    db = client[DB_NAME]
    people_collection = db.people_counting_data
    vip_vehicle_collection = db.vehicle_counting_VIP
    front_vehicle_collection = db.vehicle_counting_front
    print("✅ Successfully connected to MongoDB and all collections.")
except Exception as e:
    print(f"❌ Error connecting to MongoDB: {e}")
    client = None


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/api/dashboard_data')
def get_dashboard_data():
    if not client:
        return jsonify({"error": "Database connection failed"}), 500

    try:
        # Check if filter parameters are provided in the request
        is_filtered_request = 'start_date' in request.args and request.args['start_date']

        # --- LOGIC FOR FILTERED REQUEST ---
        if is_filtered_request:
            # Get start and end datetime from request arguments
            start_date_str = request.args.get('start_date')
            start_time_str = request.args.get('start_time') or '00:00'
            end_date_str = request.args.get('end_date')
            end_time_str = request.args.get('end_time') or '23:59'

            start_dt = datetime.strptime(f"{start_date_str} {start_time_str}", '%Y-%m-%d %H:%M')
            end_dt = datetime.strptime(f"{end_date_str} {end_time_str}", '%Y-%m-%d %H:%M')

            # 1. Filter People Data (by date range only)
            people_data_doc = people_collection.find_one({"_id": "full_dashboard_data"}, {'data': 1})
            total_people_in = 0
            total_people_out = 0
            if people_data_doc and 'data' in people_data_doc:
                for date_key, daily_data in people_data_doc['data'].items():
                    try:
                        current_date = datetime.strptime(date_key, '%Y-%m-%d')
                        # Check if the date from the DB is within the requested date range
                        if start_dt.date() <= current_date.date() <= end_dt.date():
                            for stream_data in daily_data.values():
                                total_people_in += stream_data.get('in_count', 0)
                                total_people_out += stream_data.get('out_count', 0)
                    except ValueError:
                        continue # Skip malformed date keys

            # 2. Filter Vehicle Data (by precise datetime range)
            def filter_vehicles(collection, start_dt, end_dt):
                doc = collection.find_one({"_id": "vehicle_count_data"}, {'data': 1})
                if not (doc and 'data' in doc):
                    return 0
                
                count = 0
                for vehicle in doc['data']:
                    try:
                        # Make sure timestamp exists and is a string before parsing
                        ts_str = vehicle.get("Timestamp")
                        if isinstance(ts_str, str):
                            vehicle_ts = datetime.strptime(ts_str, '%Y-%m-%d %H:%M:%S')
                            if start_dt <= vehicle_ts <= end_dt:
                                count += 1
                    except (ValueError, TypeError):
                        continue # Skip entries with missing or malformed timestamps
                return count

            vip_vehicle_count = filter_vehicles(vip_vehicle_collection, start_dt, end_dt)
            front_gate_vehicle_count = filter_vehicles(front_vehicle_collection, start_dt, end_dt)

        # --- LOGIC FOR LIVE (DEFAULT) REQUEST ---
        else:
            # This is the original logic for "today"
            people_data_doc = people_collection.find_one({"_id": "full_dashboard_data"})
            total_people_in = 0
            total_people_out = 0
            if people_data_doc and 'data' in people_data_doc:
                today_str = datetime.now().strftime('%Y-%m-%d')
                data_for_today = people_data_doc.get('data', {}).get(today_str)
                if data_for_today:
                    for stream_data in data_for_today.values():
                        total_people_in += stream_data.get('in_count', 0)
                        total_people_out += stream_data.get('out_count', 0)

            vip_vehicle_data = vip_vehicle_collection.find_one({"_id": "vehicle_count_data"})
            vip_vehicle_count = len(vip_vehicle_data.get('data', [])) if vip_vehicle_data else 0

            front_vehicle_doc = front_vehicle_collection.find_one({"_id": "vehicle_count_data"})
            front_gate_vehicle_count = len(front_vehicle_doc.get('data', [])) if front_vehicle_doc else 0

        # --- Final calculations are the same for both scenarios ---
        estimated_people_from_vehicles = vip_vehicle_count * 4
        cumulative_total = total_people_in + estimated_people_from_vehicles

        response_data = {
            "people_in": total_people_in,
            "people_out": total_people_out,
            "vehicle_count": vip_vehicle_count,
            "estimated_people_from_vehicles": estimated_people_from_vehicles,
            "cumulative_total": cumulative_total,
            "front_gate_vehicle_count": front_gate_vehicle_count
        }
        
        return jsonify(response_data)

    except Exception as e:
        import traceback
        print(f"Error in API endpoint: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# --- Run the App ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)