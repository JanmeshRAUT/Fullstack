import React, { useEffect, useRef, useState } from "react";
import { Wifi, WifiOff, UserMinus } from "lucide-react";
import { useFatigueData } from "../hooks/useFatigueData";
import { API_BASE } from "../api";

export default function CameraModule() {
  const data = useFatigueData();

  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [cameraStatus, setCameraStatus] = useState("Idle");

  const noFaceDetected = data.status === "No Face";

  useEffect(() => {
    let stream;
    let frameInterval;

    async function startCamera() {
      try {
        setCameraStatus("Starting...");
        stream = await navigator.mediaDevices.getUserMedia({ video: true });
        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          setCameraStatus("Streaming");
        }

        frameInterval = setInterval(() => {
          sendFrameToBackend();
        }, 800);
      } catch (err) {
        console.error("Camera access error:", err);
        setCameraStatus("Error");
      }
    }

    startCamera();

    return () => {
      if (frameInterval) clearInterval(frameInterval);
      if (stream) stream.getTracks().forEach((t) => t.stop());
    };
  }, []);

  const sendFrameToBackend = async () => {
    if (!videoRef.current || !canvasRef.current) return;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");

    // OPTIMIZATION: Downscale image to 480px width to prevent Backend Worker Timeout/Crash
    const scaleFactor = 480 / videoRef.current.videoWidth;
    canvas.width = 480; 
    canvas.height = videoRef.current.videoHeight * scaleFactor;
    
    ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

    // Compress to JPEG 0.5 quality (further reduces payload size)
    const imageData = canvas.toDataURL("image/jpeg", 0.5);

    try {
      const response = await fetch(`${API_BASE}/process_frame`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ image_data: imageData }),
      });
      if (!response.ok) throw new Error("Failed");
    } catch (err) {
      console.error("Frame send error:", err);
    }
  };

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
