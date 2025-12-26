import axios from "axios";

const API_BASE = "http://localhost:5000"; // Flask backend

export const getTemperature = async () => {
  try {
    const res = await axios.get(`${API_BASE}/temperature`);
    return res.data;
  } catch (err) {
    console.error("Temperature fetch error:", err);
    return null;
  }
};

export const getTemperatureHistory = async () => {
  try {
    const res = await axios.get(`${API_BASE}/temperature/history`);
    return res.data;
  } catch (err) {
    console.error("Temperature history fetch error:", err);
    return [];
  }
};

export const getPerclos = async () => {
  try {
    const res = await axios.get(`${API_BASE}/perclos`);
    return res.data;
  } catch (err) {
    console.error("PERCLOS fetch error:", err);
    return { status: "API Error", perclos: 0.0, timestamp: Date.now() };
  }
};

export async function getLatestTemperature() {
  try {
    const response = await fetch(`${API_BASE}/temperature/latest`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error("Failed to fetch latest temperature:", error);
    return null;
  }
}

export const resetCalibration = async () => {
    try {
        await axios.post(`${API_BASE}/reset_calibration`);
        return true;
    } catch (err) {
        console.error("Calibration reset failed:", err);
        return false;
    }
};
