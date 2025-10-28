import { useState, useEffect } from 'react';

export const useCombinedData = () => {
  const [data, setData] = useState({
    temperature: null,
    perclos: null,
    status: 'Loading...',
    timestamp: null,
    history: []
  });

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [sensorRes, perclosRes] = await Promise.all([
          fetch('http://localhost:5000/sensor_data'),
          fetch('http://localhost:5000/perclos')
        ]);

        const sensorData = await sensorRes.json();
        const perclosData = await perclosRes.json();

        setData(prev => ({
          temperature: sensorData.temperature,
          perclos: perclosData.perclos,
          status: perclosData.status,
          timestamp: Date.now(),
          history: [...prev.history.slice(-19), {
            time: new Date().toLocaleTimeString(),
            temperature: sensorData.temperature,
            perclos: perclosData.perclos
          }]
        }));
      } catch (error) {
        console.error('Error fetching data:', error);
      }
    };

    fetchData();
    const interval = setInterval(fetchData, 3000);
    return () => clearInterval(interval);
  }, []);

  return data;
};
