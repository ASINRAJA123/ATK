from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime
import traceback

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
        # --- Get People Data and Last Updated Time ---
        people_data_doc = people_collection.find_one({"_id": "full_dashboard_data"})
        total_people_in = 0
        total_people_out = 0
        stream_0_last_updated = "N/A"  # Default value in case it's not found

        if people_data_doc and 'data' in people_data_doc:
            today_str = datetime.now().strftime('%Y-%m-%d')
            data_for_today = people_data_doc.get('data', {}).get(today_str)
            
            if data_for_today:
                # Calculate total in/out from all streams for the day
                for stream_data in data_for_today.values():
                    total_people_in += stream_data.get('in_count', 0)
                    total_people_out += stream_data.get('out_count', 0)
                
                # --- NEW: Get last_updated specifically from stream_0 ---
                # Safely access the nested value using .get() to prevent errors
                if 'stream_0' in data_for_today:
                    stream_0_last_updated = data_for_today.get('stream_0', {}).get('last_updated', 'N/A')

        # --- Get Vehicle Data ---
        front_vehicle_doc = front_vehicle_collection.find_one({"_id": "vehicle_count_data"})
        front_gate_vehicle_count = len(front_vehicle_doc.get('data', [])) if front_vehicle_doc else 0

        vehicle_counts = {"motorcycle": 0, "car": 0, "truck": 0, "bus": 0, "total": 0}
        estimated_people_from_vehicles = 0
        vehicle_multipliers = {"motorcycle": 2, "car": 4, "truck": 10, "bus": 20}
        
        vip_vehicle_doc = vip_vehicle_collection.find_one({"_id": "vehicle_count_data"})
        if vip_vehicle_doc and 'data' in vip_vehicle_doc:
            all_vehicles = vip_vehicle_doc.get('data', [])
            vehicle_counts["total"] = len(all_vehicles)
            for vehicle in all_vehicles:
                v_class = vehicle.get("Class", "").lower()
                if v_class in vehicle_counts:
                    vehicle_counts[v_class] += 1
                estimated_people_from_vehicles += vehicle_multipliers.get(v_class, 0)
        
        # --- Final calculations and Response ---
        cumulative_total = total_people_in + estimated_people_from_vehicles

        response_data = {
            "people_in": total_people_in,
            "people_out": total_people_out,
            "vehicle_counts": vehicle_counts,
            "estimated_people_from_vehicles": estimated_people_from_vehicles,
            "cumulative_total": cumulative_total,
            "front_gate_vehicle_count": front_gate_vehicle_count,
            "stream_0_last_updated": stream_0_last_updated  # Add the new data point to the response
        }
        
        return jsonify(response_data)

    except Exception as e:
        print(f"Error in API endpoint: {e}")
        traceback.print_exc()
        return jsonify({"error": str(e)}), 500

# --- Run the App ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
