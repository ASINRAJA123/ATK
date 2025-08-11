from flask import Flask, jsonify, render_template
from flask_cors import CORS
from pymongo import MongoClient
from datetime import datetime # <-- Step 1: Import datetime

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
    vehicle_collection = db.vehicle_counting_VIP
    print("✅ Successfully connected to MongoDB.")
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
        # ===================================================================
        # MODIFIED LOGIC FOR PEOPLE COUNTING
        # ===================================================================

        people_data_doc = people_collection.find_one({"_id": "full_dashboard_data"})
        
        total_people_in = 0
        total_people_out = 0
        
        if people_data_doc and 'data' in people_data_doc:
            # Step 2: Get today's date and format it to match the DB key 'YYYY-MM-DD'
            today_str = datetime.now().strftime('%Y-%m-%d')
            
            # --- For Testing Purposes ---
            # Since your sample data is for 2025, uncomment the line below 
            # to test the logic with a date that exists in your data.
            # today_str = "2025-08-08" 
            
            print(f"Fetching people count data for date: {today_str}")

            # Step 3: Safely get the data object for the current day.
            # .get(today_str, {}) will return the day's data or an empty dict if the date key doesn't exist.
            all_data_fields = people_data_doc.get('data', {})
            data_for_today = all_data_fields.get(today_str)

            # Step 4: If data exists for today, iterate through its streams and sum the counts.
            if data_for_today and isinstance(data_for_today, dict):
                # The data for a day contains stream objects like "stream_0", "stream_1"
                for stream_name, stream_data in data_for_today.items():
                    if isinstance(stream_data, dict):
                        total_people_in += stream_data.get('in_count', 0)
                        total_people_out += stream_data.get('out_count', 0)

        # ===================================================================
        # Vehicle counting logic remains the same
        # ===================================================================
        vehicle_data = vehicle_collection.find_one({"_id": "vehicle_count_data"})
        
        vehicle_count = 0
        if vehicle_data and 'data' in vehicle_data:
            vehicle_count = len(vehicle_data.get('data', []))
            
        # ===================================================================
        # Final calculations remain the same
        # ===================================================================
        estimated_people_from_vehicles = vehicle_count * 4
        
        # Cumulative total uses the people IN for TODAY plus vehicle estimates
        cumulative_total = total_people_in + estimated_people_from_vehicles

        # Prepare the response JSON
        response_data = {
            "people_in": total_people_in,
            "people_out": total_people_out,
            "vehicle_count": vehicle_count,
            "estimated_people_from_vehicles": estimated_people_from_vehicles,
            "cumulative_total": cumulative_total
        }
        
        return jsonify(response_data)

    except Exception as e:
        print(f"Error in API endpoint: {e}") # Added more detailed logging
        return jsonify({"error": str(e)}), 500


# --- Run the App ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)