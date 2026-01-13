import { useFatigueContext } from "../context/FatigueContext"; // Import Context directly for actions

export default function CameraModule() {
  const data = useFatigueData();
  const { updateRealTimeData } = useFatigueContext(); // Get the updater action

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [cameraStatus, setCameraStatus] = useState("Idle");

  const noFaceDetected = data.status === "No Face";

  useEffect(() => {
    let stream;
    let frameInterval;
    let ws;

    async function startCamera() {
      try {
        setCameraStatus("Starting...");
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
        }
        
        // Initialize WebSocket
        try {
            const wsBase = API_BASE.replace(/^http/, 'ws');
            const wsUrl = `${wsBase}/ws/detect`;
            ws = new WebSocket(wsUrl);
            console.log("Connecting to WS:", wsUrl);
            
            ws.onopen = () => {
                console.log("WebSocket Connected");
                setCameraStatus("Streaming");
                
                // Start sending frames ONLY when WS is open
                frameInterval = setInterval(() => {
                    sendFrameOverSocket(ws);
                }, 100); // 10 FPS
            };

            ws.onmessage = (event) => {
                try {
                    const result = JSON.parse(event.data);
                    if (result && !result.error) {
                         // Update global state with fast real-time data
                         updateRealTimeData(result);
                    }
                } catch (e) {
                    // Ignore parse errors
                }
            };

            ws.onclose = () => {
                console.log("WebSocket Disconnected");
                setCameraStatus("Disconnected");
            };

            ws.onerror = (err) => {
                console.error("WebSocket Error:", err);
                setCameraStatus("Error");
            };

        } catch (wsErr) {
            console.error("WS Setup Error:", wsErr);
            setCameraStatus("Error");
        }

      } catch (err) {
        console.error("Camera access error:", err);
        setCameraStatus("Error");
      }
    }

    const sendFrameOverSocket = (socket) => {
        if (!videoRef.current || !canvasRef.current || socket.readyState !== WebSocket.OPEN) return;
        
        const canvas = canvasRef.current;
        const ctx = canvas.getContext("2d");

        // OPTIMIZATION: Downscale image to 480px width
        const scaleFactor = 480 / videoRef.current.videoWidth;
        canvas.width = 480; 
        canvas.height = videoRef.current.videoHeight * scaleFactor;
        
        ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

        // Compress to JPEG 0.5 quality
        const imageData = canvas.toDataURL("image/jpeg", 0.5);
        
        socket.send(imageData);
    };

    startCamera();

    return () => {
      if (frameInterval) clearInterval(frameInterval);
      if (ws) ws.close();
      if (stream) stream.getTracks().forEach((t) => t.stop());
    };
  }, []);

  return (
    <>
      <div style={{ width: '100%', height: '100%', position: 'relative', overflow: 'hidden', borderRadius: '12px' }}>
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="camera-feed-video"
          style={{ transform: "scaleX(-1)", width: '100%', height: '100%', objectFit: 'cover' }}
        />
        <canvas ref={canvasRef} style={{ display: "none" }} />

        {/* NO FACE DETECTED OVERLAY */}
        {noFaceDetected && cameraStatus === 'Streaming' && (
          <div style={{
            position: 'absolute',
            inset: 0,
            background: 'rgba(239, 68, 68, 0.2)', 
            backdropFilter: 'blur(2px)',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 20
          }}>
            <div className="animate-pulse" style={{ background: '#ef4444', padding: '8px 16px', borderRadius: '8px', color: 'white', fontWeight: 800, fontSize: '0.9rem', display: 'flex', alignItems: 'center', gap: '8px', boxShadow: '0 4px 12px rgba(239, 68, 68, 0.4)' }}>
              <UserMinus size={18} strokeWidth={3} />
              NO FACE DETECTED
            </div>
            <span style={{ color: 'white', fontSize: '0.7rem', fontWeight: 600, marginTop: '8px', textShadow: '0 1px 2px rgba(0,0,0,0.5)' }}>Center yourself in the frame</span>
          </div>
        )}

        {/* Overlay HUD */}
        <div className="camera-overlay">
          <div className="camera-status">
            <span style={{
              width: 8, height: 8, borderRadius: '50%',
              background: cameraStatus === 'Streaming' ? (noFaceDetected ? '#f59e0b' : '#22c55e') : '#ef4444'
            }}></span>
            {cameraStatus === 'Streaming' ? (noFaceDetected ? 'Searching...' : 'Live Feed Active') : 'Feed Interrupted'}
          </div>

          <div>
            {cameraStatus === 'Streaming' ? <Wifi size={16} /> : <WifiOff size={16} />}
          </div>
        </div>
      </div>
    </>
  );
}
