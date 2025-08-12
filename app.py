from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime

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
        # --- LOGIC FOR LIVE (TODAY'S) DATA ---

        # 1. Get People Data for Today
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

        # 2. Get Total Vehicle Counts (as per original live logic)
        vip_vehicle_data = vip_vehicle_collection.find_one({"_id": "vehicle_count_data"})
        vip_vehicle_count = len(vip_vehicle_data.get('data', [])) if vip_vehicle_data else 0

        front_vehicle_doc = front_vehicle_collection.find_one({"_id": "vehicle_count_data"})
        front_gate_vehicle_count = len(front_vehicle_doc.get('data', [])) if front_vehicle_doc else 0

        # --- Final calculations ---
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