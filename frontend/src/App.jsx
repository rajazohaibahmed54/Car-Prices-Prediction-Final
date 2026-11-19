import { useState } from "react";
import LoginView from "./LoginView";
import "./App.css";

function App() {
  const [token, setToken] = useState("");

  const [formData, setFormData] = useState({
    Model: "",
    CC: "",
    Engine_type: "Petrol",
    Transmission: "Automatic",
    Km_Driven: "",
  });

  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setResult(null);
    setLoading(true);

    try {
      const response = await fetch("http://127.0.0.1:5000/predict", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({
          Model: formData.Model.trim(),
          CC: Number(formData.CC),
          Engine_type: formData.Engine_type,
          Transmission: formData.Transmission,
          Km_Driven: Number(formData.Km_Driven),
        }),
      });

      const data = await response.json();

      if (!response.ok) {
        setError(data.error || "Prediction failed.");
      } else {
        setResult(data);
      }
    } catch (err) {
      setError("Could not connect to Flask backend. Make sure app.py is running.");
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return <LoginView onLoginSuccess={(receivedToken) => setToken(receivedToken)} />;
  }

  return (
    <div className="container">
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <h2>Car Price Prediction</h2>
        <button
          type="button"
          onClick={() => {
            setToken("");
            setResult(null);
            setError("");
          }}
        >
          Log Out
        </button>
      </div>

      <form onSubmit={handleSubmit}>
        <div>
          <label>Car Model</label>
          <input
            type="text"
            name="Model"
            value={formData.Model}
            onChange={handleChange}
            placeholder="e.g. Corolla Altis 1.6"
            required
          />
        </div>

        <div>
          <label>Engine Displacement (CC)</label>
          <input
            type="number"
            step="any"
            name="CC"
            value={formData.CC}
            onChange={handleChange}
            placeholder="e.g. 1600"
            required
          />
        </div>

        <div>
          <label>Engine Type</label>
          <select
            name="Engine_type"
            value={formData.Engine_type}
            onChange={handleChange}
          >
            <option value="Petrol">Petrol</option>
            <option value="Hybrid">Hybrid</option>
            <option value="Diesel">Diesel</option>
            <option value="Electric">Electric</option>
            <option value="CNG">CNG</option>
          </select>
        </div>

        <div>
          <label>Transmission</label>
          <select
            name="Transmission"
            value={formData.Transmission}
            onChange={handleChange}
          >
            <option value="Automatic">Automatic</option>
            <option value="Manual">Manual</option>
          </select>
        </div>

        <div>
          <label>KM Driven</label>
          <input
            type="number"
            step="any"
            name="Km_Driven"
            value={formData.Km_Driven}
            onChange={handleChange}
            placeholder="e.g. 45000"
            required
          />
        </div>

        <button type="submit" disabled={loading}>
          {loading ? "Predicting..." : "Predict Price"}
        </button>
      </form>

      {error && <div className="error-box">{error}</div>}

      {result && (
        <div className="result-box">
          <p className="result-price">{result.prediction_text}</p>
          <p className="result-range">{result.range_text}</p>
        </div>
      )}
    </div>
  );
}

export default App;