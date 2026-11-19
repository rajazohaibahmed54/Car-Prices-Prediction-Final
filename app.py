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

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json() or {}
    if data.get("username") == SECRET_USER and data.get("password") == SECRET_PASS:
        return jsonify({"token": SECRET_TOKEN})
    return jsonify({"error": "Wrong username or password"}), 401

@app.route('/predict', methods=['POST'])
@check_login
def predict():
    try:
        data = request.get_json()

        # 1. Get data sent from React
        car_model = data['Model']
        cc = float(data['CC'])
        engine_type = data['Engine_type']
        transmission = data['Transmission']
        km_driven = float(data['Km_Driven'])

        # 2. Prepare input for the model
        input_data = pd.DataFrame([[car_model, cc, engine_type, transmission, km_driven]],
                                  columns=['Model', 'CC', 'Engine_type', 'Transmission', 'Km_Driven'])

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