import axios from "axios";

// Environment Configuration
export const API_BASE = process.env.REACT_APP_API_URL || "https://nulliporous-carbolic-lianne.ngrok-free.dev";

// Initialize Axios Instance
// We use a specific instance rather than the global axios object to avoid conflicts/pollution
const apiClient = axios.create({
  baseURL: API_BASE,
  headers: {
    'Content-Type': 'application/json',
    'ngrok-skip-browser-warning': 'true'
  }
});

// Debug Log
console.log(`[API] Initialized with Base URL: ${API_BASE}`);

// --- API FUNCTIONS ---

export const getTemperature = async () => {
  try {
    const res = await apiClient.get('/temperature');
    return res.data;
  } catch (err) {
    console.error("[API] getTemperature Error:", err);
    return null;
  }
};

export const getTemperatureHistory = async () => {
  try {
    const res = await apiClient.get('/temperature/history');
    return res.data;
  } catch (err) {
    console.error("[API] getTemperatureHistory Error:", err);
    return [];
  }
};

export const getPerclos = async () => {
  try {
    const res = await apiClient.get('/perclos');
    return res.data;
  } catch (err) {
    console.error("[API] getPerclos Error:", err);
    // Return safe fallback object
    return { status: "API Error", perclos: 0.0, timestamp: Date.now() };
  }
};

export async function getLatestTemperature() {
  try {
    const response = await apiClient.get('/temperature/latest');
    return response.data;
  } catch (error) {
    console.error("[API] getLatestTemperature Error:", error);
    return null;
  }
}

export const resetCalibration = async () => {
    try {
        await apiClient.post('/reset_calibration');
        return true;
    } catch (err) {
        console.error("[API] resetCalibration Error:", err);
        return false;
    }
};

export const checkBackendHealth = async () => {
    try {
        const start = Date.now();
        const res = await apiClient.get('/health');
        const latency = Date.now() - start;
        return { 
            status: "Online", 
            latency, 
            version: res.data.service || "unknown" 
        };
    } catch (err) {
        console.error("[API] checkBackendHealth Error:", err);
        return { status: "Offline", latency: 0 };
    }
};
