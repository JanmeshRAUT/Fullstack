import React, { useEffect, useRef, useState } from "react";
import { Wifi, WifiOff } from "lucide-react";

export default function CameraModule() {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [cameraStatus, setCameraStatus] = useState("Idle");

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

        // Send frames to Flask backend
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

    canvas.width = videoRef.current.videoWidth;
    canvas.height = videoRef.current.videoHeight;
    ctx.drawImage(videoRef.current, 0, 0, canvas.width, canvas.height);

    const imageData = canvas.toDataURL("image/jpeg", 0.6);

    try {
      const response = await fetch("http://127.0.0.1:5000/process_frame", {
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
      {/* Video Feed */}
      <div style={{width: '100%', height: '100%', position: 'relative'}}>
         <video
            ref={videoRef}
            autoPlay
            playsInline
            muted
            className="camera-feed-video" 
            style={{ transform: "scaleX(-1)" }} // Mirror effect
         />
         <canvas ref={canvasRef} style={{ display: "none" }} />
         
         {/* Overlay */}
         <div className="camera-overlay">
           <div className="camera-status">
              <span style={{
                width: 8, height: 8, borderRadius: '50%', 
                background: cameraStatus === 'Streaming' ? '#22c55e' : '#ef4444'
              }}></span>
              {cameraStatus === 'Streaming' ? 'Live Feed Active' : 'Feed Interrupted'}
           </div>
           
           <div>
              {cameraStatus === 'Streaming' ? <Wifi size={16} /> : <WifiOff size={16} />}
           </div>
         </div>
      </div>
    </>
  );
}
