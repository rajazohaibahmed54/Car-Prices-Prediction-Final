#We will us the Monte Carlo simulation to predict the price of a car based on the features used in our model. We will generate random values for the features and use the model to predict the price of the car for each set of features. This will allow us to understand the distribution of predicted prices and make informed decisions based on that distribution.
import joblib
import numpy as np
import pandas as pd 
import matplotlib.pyplot as plt

#Loading the model 
model=joblib.load('model\car_price_model.pkl')

#defining a test case for the model, to get the deterministic price of the car based on the features used in our model. We will use this test case to compare the results of our Monte Carlo simulation.
test_case = pd.DataFrame([{
    'Km_Driven': 150000.0,
    'CC': 1500.0,
    'Title': 'Honda Civic',
    'Model': 1994,
    'Transmission': 'Manual',
    'Engine_type' :'Petrol'
}])
base_pred = model.predict(test_case)[0]
print(f"Base Predicted Price: {base_pred:,.0f} PKR")

#Monte Carlo Simulation
#Assuming from the internet that the car market for this specific vehicle fluctuates at the rate of 10% up and down, we will generate random values for the features within this range and use the model to predict the price of the car for each set of features. We will run the simulation for 5000 iterations to get a good distribution of predicted prices.

iterations= 5000
market_fluctuation= np.random.uniform(0.9,1.1, iterations)

# Generate Gaussian Noise (Standard Deviation of 50,000 PKR)
# This represents the "unseen" condition of the specific car
condition_noise = np.random.normal(0, 50000, iterations)

# Calculate the predicted prices based on the base prediction, market fluctuation, and condition noise
predicted_prices = base_pred * market_fluctuation + condition_noise

#now instead of calculating one price we will generate a confidence score
# Calculate 95% Confidence Interval (2.5th and 97.5th percentiles)
lower_ci = np.percentile(predicted_prices, 2.5)
upper_ci = np.percentile(predicted_prices, 97.5)

print(f"95% Confidence Interval: {lower_ci:,.0f} to {upper_ci:,.0f} PKR")
# Plotting the distribution of predicted prices
plt.style.use('ggplot')
plt.figure(figsize=(10, 6))
plt.hist(predicted_prices, bins=50, color='#2ecc71', alpha=0.7, edgecolor='white')
plt.axvline(base_pred, color='blue', linestyle='--', label=f'Original Prediction: {base_pred:,.0f}')
plt.axvline(lower_ci, color='red', label='Lower Bound (95%)')
plt.axvline(upper_ci, color='red', label='Upper Bound (95%)')

plt.title("AutoValuate: Probabilistic Price Distribution")
plt.xlabel("Price in PKR")
plt.ylabel("Probability Density")
plt.legend()
plt.show()