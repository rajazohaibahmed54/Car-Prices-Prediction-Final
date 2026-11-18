from flask import Flask, render_template, request
import pickle
import pandas as pd
import numpy as np

app = Flask(__name__)

try:
    with open('model/car_price_model.pkl', 'rb') as file:
        model = pickle.load(file)
except FileNotFoundError:
    print("Error: Model file not found. Make sure 'car_price_model.pkl' is in the 'model' folder.")
    exit()

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/predict', methods=['POST'])
def predict():
    # 1. Get data from the HTML form
    car_model = request.form['Model']
    cc = float(request.form['CC'])    
    engine_type = request.form['Engine_type']
    transmission = request.form['Transmission']
    km_driven = float(request.form['Km_Driven'])

    # 2. Prepare input for the model
    input_data = pd.DataFrame([[car_model, cc, engine_type, transmission, km_driven]],
                              columns=['Model', 'CC', 'Engine_type', 'Transmission', 'Km_Driven'])

    # 3. Base Prediction
    prediction = model.predict(input_data)
    base_price = prediction[0]

    # --- MONTE CARLO & NOISE MODELING START ---
    iterations = 2000
    
    # Noise Model 1: Market Volatility (Uniform Noise)
    # Simulates +/- 10% market fluctuations (e.g., fuel price changes)
    market_noise = np.random.uniform(0.90, 1.10, iterations)
    
    # Noise Model 2: Condition Uncertainty (Gaussian Noise)
    # Simulates hidden wear/tear (Standard Deviation of 40,000 PKR)
    condition_noise = np.random.normal(0, 40000, iterations)
    
    # Generate the simulated price distribution
    predicted_prices = (base_price * market_noise) + condition_noise

    # Calculate 95% Confidence Intervals
    low_price = np.percentile(predicted_prices, 2.5)
    high_price = np.percentile(predicted_prices, 97.5)
    # --- MONTE CARLO & NOISE MODELING END ---

    # Formatting Results
    price_in_lacs = round(base_price / 100000, 2)
    low_lacs = round(low_price / 100000, 2)
    high_lacs = round(high_price / 100000, 2)
    
    result_text = f"Estimated Price: PKR {base_price:,.0f} ({price_in_lacs} Lacs)"
    range_text = f"Probabilistic Range: PKR {low_price:,.0f} - {high_price:,.0f} ({low_lacs} - {high_lacs} Lacs)"

    return render_template('index.html', 
                           prediction_text=result_text, 
                           range_text=range_text)

if __name__ == '__main__':
    app.run(debug=True)