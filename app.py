# app.py

from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
import pandas as pd
import joblib
import os
import json
import requests

app = Flask(__name__)
app.secret_key = 'your_super_secret_key_change_this'

# --- Mock Databases ---
MOCK_USERS = {"admin": "password123"}
projects_db = [
    {'id': 1, 'name': 'Shimla North Corridor', 'status': 'Ongoing', 'budget': 1535},
    {'id': 2, 'name': 'Mumbai Metro Grid', 'status': 'Planning', 'budget': 332},
    {'id': 3, 'name': 'Jaipur Rural Expansion', 'status': 'Completed', 'budget': 996},
    {'id': 4, 'name': 'Kolkata East Link', 'status': 'Ongoing', 'budget': 780},
    {'id': 5, 'name': 'Gujarat Coastal Project', 'status': 'Planning', 'budget': 1120},
    {'id': 6, 'name': 'Assam Valley Connection', 'status': 'Completed', 'budget': 450}
]
materials_db = [
    {'id': 'Steel_Tons', 'name': 'Steel', 'category': 'Tower & Foundation', 'stock': 300, 'unit': 'Tons', 'reorder_level': 100, 'cost': 75000, 'supplier': 'TATA Steel', 'status': 'In Stock'},
    {'id': 'Conductor_KM', 'name': 'Conductor', 'category': 'Transmission Line', 'stock': 50, 'unit': 'KM', 'reorder_level': 20, 'cost': 207500, 'supplier': 'Sterlite Power', 'status': 'Low Stock'},
    {'id': 'Insulators_Units', 'name': 'Insulators', 'category': 'Sub-station Fittings', 'stock': 25000, 'unit': 'Units', 'reorder_level': 5000, 'cost': 1250, 'supplier': 'Aditya Birla Insulators', 'status': 'In Stock'}
]

MODEL_PATH = 'demand_forecaster.joblib'
model = joblib.load(MODEL_PATH) if os.path.exists(MODEL_PATH) else None

# --- Complete mapping of States to Cities ---
state_city_map = {
    "Andhra Pradesh": ["Guntur", "Tirupati", "Vijayawada", "Visakhapatnam", "Warangal"],
    "Arunachal Pradesh": ["Bomdila", "Itanagar", "Tawang", "Ziro"], "Assam": ["Guwahati"], "Bihar": ["Bodh Gaya", "Gaya", "Patna"], "Chandigarh": ["Chandigarh"],
    "Chhattisgarh": ["Raipur"], "Delhi": ["Delhi"], "Goa": ["Goa"],
    "Gujarat": ["Ahmedabad", "Bhavnagar", "Gandhinagar", "Rajkot", "Surat", "Vadodara"], "Haryana": ["Bahadurgarh", "Faridabad", "Gurgaon"],
    "Himachal Pradesh": ["Dalhousie", "Dharamshala", "Kasauli", "Kufri", "Manali", "Shimla", "Spiti"],
    "Jammu and Kashmir": ["Gulmarg", "Leh", "Pahalgam", "Sonamarg", "Srinagar", "Turtuk", "Nubra Valley"], "Jharkhand": ["Dhanbad", "Jamshedpur", "Ranchi"],
    "Karnataka": ["Bangalore", "Gokarna", "Hampi", "Mysore"], "Kerala": ["Kochi", "Munnar", "Thiruvananthapuram"],
    "Madhya Pradesh": ["Bhopal", "Gwalior", "Indore", "Jabalpur", "Khajuraho", "Orchha", "Sanchi", "Ujjain"],
    "Maharashtra": ["Aurangabad", "Kolhapur", "Lonavla", "Mahabaleshwar", "Matheran", "Mumbai", "Nagpur", "Nashik", "Navi Mumbai", "Pune", "Solapur", "Thane"],
    "Meghalaya": ["Shillong"], "Mizoram": ["Aizawl"], "Odisha": ["Bhubaneswar", "Puri"], "Puducherry": ["Pondicherry"], "Punjab": ["Amritsar", "Jalandhar", "Ludhiana"],
    "Rajasthan": ["Ajmer", "Bikaner", "Jaipur", "Jaisalmer", "Jodhpur", "Kota", "Pushkar", "Udaipur"], "Sikkim": ["Gangtok", "Lachung", "Lava", "Loleygaon", "Pelling", "Ravangla", "Yuksom", "Zuluk"],
    "Tamil Nadu": ["Chennai", "Coimbatore", "Kodaikanal", "Madurai"], "Telangana": ["Hyderabad", "Secunderabad"],
    "Uttar Pradesh": ["Agra", "Aligarh", "Allahabad", "Ayodhya", "Bareilly", "Firozabad", "Ghaziabad", "Hathras", "Jhansi", "Kanpur", "Lucknow", "Mathura", "Meerut", "Moradabad", "Noida", "Rampur", "Saharanpur", "Sarnath", "Varanasi", "Vrindavan"],
    "Uttarakhand": ["Almora", "Auli", "Chaukori", "Chopta", "Dehradun", "Haridwar", "Kausani", "Lohaghat", "Mukteshwar", "Munsiyari", "Mussoorie", "Nainital", "Pithoragarh", "Rishikesh"],
    "West Bengal": ["Bakkhali", "Bishnupur", "Darjeeling", "Digha", "Durgapur", "Gaur", "Kalimpong", "Kolkata", "Mandarmoni", "Shantiniketan", "Siliguri"]
}

BASE_MATERIAL_PRICES_USD = { "Steel_Tons": 900, "Conductor_KM": 2500, "Insulators_Units": 15 }

def get_live_inr_rate():
    API_KEY = "9938617f132776a907ed676b"
    try:
        url = f"https://v6.exchangerate-api.com/v6/{API_KEY}/latest/USD"; response = requests.get(url, timeout=5)
        response.raise_for_status(); data = response.json(); inr_rate = data['conversion_rates']['INR']
        print(f"✅ API SUCCESS: Fetched live exchange rate: 1 USD = ₹{inr_rate:.2f}"); return inr_rate
    except Exception as e:
        print(f"❌ API ERROR: Could not fetch exchange rate. Using default. Error: {e}"); return 83.5

# --- Page Routes (Full Implementations) ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']; password = request.form['password']
        if username in MOCK_USERS and MOCK_USERS[username] == password:
            session['username'] = username; return redirect(url_for('dashboard'))
        else: flash('Invalid credentials. Please try again.')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('username', None); return redirect(url_for('login'))
    
@app.route('/')
def dashboard():
    if 'username' not in session: return redirect(url_for('login'))
    total_projects = len(projects_db)
    ongoing_projects = len([p for p in projects_db if p['status'] == 'Ongoing'])
    total_budget = sum(p['budget'] for p in projects_db)
    chart_labels = [p['name'] for p in projects_db]
    chart_data = [p['budget'] for p in projects_db]
    return render_template('index.html', total_projects=total_projects, ongoing_projects=ongoing_projects, total_budget=total_budget, chart_labels=json.dumps(chart_labels), chart_data=json.dumps(chart_data), session=session)

@app.route('/projects')
def projects():
    if 'username' not in session: return redirect(url_for('login'))
    return render_template('projects.html', projects=projects_db, session=session)

@app.route('/materials')
def materials():
    if 'username' not in session: return redirect(url_for('login'))
    inr_rate = get_live_inr_rate()
    dynamic_materials = []
    for material in materials_db:
        updated_material = material.copy()
        base_usd_price = BASE_MATERIAL_PRICES_USD.get(material['id'], 0)
        updated_material['cost'] = base_usd_price * inr_rate
        dynamic_materials.append(updated_material)
    return render_template('materials.html', materials=dynamic_materials, session=session)

@app.route('/forecasting')
def forecasting():
    if 'username' not in session: return redirect(url_for('login'))
    current_inr_rate = get_live_inr_rate()
    return render_template('forecasting.html', materials=materials_db, material_prices_json=json.dumps(BASE_MATERIAL_PRICES_USD), current_inr_rate=current_inr_rate, state_city_map_json=json.dumps(state_city_map), session=session)

@app.route('/settings')
def settings():
    if 'username' not in session: return redirect(url_for('login'))
    return render_template('settings.html', session=session)

@app.route('/api/predict_demand', methods=['POST'])
def predict_demand():
    if 'username' not in session: return jsonify({'error': 'Unauthorized'}), 401
    if not model: return jsonify({'error': 'Model not loaded'}), 500
    try:
        data = request.get_json()
        live_inr_price = float(data['unit_price'])
        material_type = data['material']
        input_df = pd.DataFrame({
            'project_location': [data['project_location']], 'geographic_location': [data['geographic_location']], 'tower_type': [data['tower_type']], 'budget_crore_inr': [float(data['budget'])],
            'project_duration_months': [int(data['duration'])], 'seasonality_factor': [data['seasonality']], 'material_id': [material_type],
            'material_unit_price_inr': [live_inr_price], 'material_lead_time_days': [int(data['lead_time'])], 'service_level_requirement_pct': [float(data['service_level'])],
            'inventory_holding_cost_pct': [float(data['holding_cost'])], 'transportation_cost_pct': [float(data['transport_cost'])], 'supplier_reliability_score': [0.95],
            'market_price_volatility': ['Medium'], 'resource_availability': ['High'], 'supply_chain_disruption_risk': [5], 'historical_demand_variation_pct': [0.20]
        })
        prediction = model.predict(input_df)[0]
        output_data = { 'eoq': prediction[0], 'reorder_point': prediction[1], 'safety_stock': prediction[2], 'optimal_order_frequency_days': prediction[3], 'total_demand_quantity': prediction[4], 'total_supply_chain_cost_inr': prediction[5] }
        return jsonify(output_data)
    except Exception as e:
        print(f"Error during prediction: {e}"); return jsonify({'error': 'Failed to make prediction'}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)