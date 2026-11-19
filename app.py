from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS
import pickle
import pandas as pd
import numpy as np

app = Flask(__name__)
CORS(app)

SECRET_USER = "admin"
SECRET_PASS = "1234"
SECRET_TOKEN = "token123"

ALLOWED_ENGINE_TYPES = {"Petrol", "Diesel", "Hybrid", "Electric", "CNG"}
ALLOWED_TRANSMISSIONS = {"Automatic", "Manual"}

def check_login(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.headers.get("Authorization", "")
        if auth != f"Bearer {SECRET_TOKEN}":
            return jsonify({"error": "Not logged in"}), 401
        return f(*args, **kwargs)
    return decorated

try:
    with open('model/car_price_model_new.pkl', 'rb') as file:
        model = pickle.load(file)
except FileNotFoundError:
    print("Error: Model file not found. Make sure 'car_price_model_new.pkl' is in the 'model' folder.")
    exit()

def validate_prediction_payload(data):
    if not isinstance(data, dict):
        return None, "Invalid JSON payload"

    required_fields = ["Model", "CC", "Engine_type", "Transmission", "Km_Driven"]
    for field in required_fields:
        if field not in data or data[field] is None or str(data[field]).strip() == "":
            return None, f"{field} is required"

    car_model = str(data["Model"]).strip()
    if len(car_model) < 2 or len(car_model) > 80:
        return None, "Model must be between 2 and 80 characters"

    try:
        cc = float(data["CC"])
    except (ValueError, TypeError):
        return None, "CC must be a valid number"

    if not np.isfinite(cc) or cc < 500 or cc > 8000:
        return None, "CC must be between 500 and 8000"

    engine_type = str(data["Engine_type"]).strip()
    if engine_type not in ALLOWED_ENGINE_TYPES:
        return None, f"Engine_type must be one of: {', '.join(sorted(ALLOWED_ENGINE_TYPES))}"

    transmission = str(data["Transmission"]).strip()
    if transmission not in ALLOWED_TRANSMISSIONS:
        return None, f"Transmission must be one of: {', '.join(sorted(ALLOWED_TRANSMISSIONS))}"

    try:
        km_driven = float(data["Km_Driven"])
    except (ValueError, TypeError):
        return None, "Km_Driven must be a valid number"

    if not np.isfinite(km_driven) or km_driven < 0 or km_driven > 1000000:
        return None, "Km_Driven must be between 0 and 1,000,000"

    cleaned = {
        "Model": car_model,
        "CC": cc,
        "Engine_type": engine_type,
        "Transmission": transmission,
        "Km_Driven": km_driven,
    }
    return cleaned, None

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json(silent=True) or {}
    username = str(data.get("username", "")).strip()
    password = str(data.get("password", ""))

    if not username or not password:
        return jsonify({"error": "Username and password are required"}), 400

    if username == SECRET_USER and password == SECRET_PASS:
        return jsonify({"token": SECRET_TOKEN})
    return jsonify({"error": "Wrong username or password"}), 401

@app.route('/predict', methods=['POST'])
@check_login
def predict():
    try:
        data = request.get_json(silent=True)
        cleaned, validation_error = validate_prediction_payload(data)
        if validation_error:
            return jsonify({"error": validation_error}), 400

        # 1. Use validated data sent from React
        car_model = cleaned['Model']
        cc = cleaned['CC']
        engine_type = cleaned['Engine_type']
        transmission = cleaned['Transmission']
        km_driven = cleaned['Km_Driven']

        # 2. Prepare input for the model
        input_data = pd.DataFrame(
            [[car_model, cc, engine_type, transmission, km_driven]],
            columns=['Model', 'CC', 'Engine_type', 'Transmission', 'Km_Driven']
        )

        # 3. Base Prediction
        prediction = model.predict(input_data)
        base_price = float(prediction[0])

        # --- MONTE CARLO & NOISE MODELING START ---
        iterations = 2000
        market_noise = np.random.uniform(0.90, 1.10, iterations)
        condition_noise = np.random.normal(0, 40000, iterations)
        predicted_prices = (base_price * market_noise) + condition_noise

        low_price = float(np.percentile(predicted_prices, 2.5))
        high_price = float(np.percentile(predicted_prices, 97.5))
        # --- MONTE CARLO & NOISE MODELING END ---

        # Formatting Results
        price_in_lacs = round(base_price / 100000, 2)
        low_lacs = round(low_price / 100000, 2)
        high_lacs = round(high_price / 100000, 2)

        return jsonify({
            "prediction_text": f"Estimated Price: PKR {base_price:,.0f} ({price_in_lacs} Lacs)",
            "range_text": f"Probabilistic Range: PKR {low_price:,.0f} - {high_price:,.0f} ({low_lacs} - {high_lacs} Lacs)"
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 400

if __name__ == '__main__':
    app.run(debug=True)