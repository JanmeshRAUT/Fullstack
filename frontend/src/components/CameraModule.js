import React, { useEffect, useRef, useState } from "react";

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

        // Send frames to Flask backend every 800ms
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

  // Capture frame and send to Flask
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

      if (!response.ok) throw new Error("Failed to process frame");

    } catch (err) {
      console.error("Frame send error:", err);
    }
  };


  return (
    <div className="card camera">
      <h4>Camera Module</h4>

      <div className="camera-box">
        <video
          ref={videoRef}
          autoPlay
          playsInline
          muted
          className="camera-feed"/>
        <canvas ref={canvasRef} style={{ display: "none" }} />
      </div>
      <div style={{ marginTop: "14px", textAlign: "left" }}>
        <p>
          <strong>Status:</strong>{" "}
          <span style={{ color: "#60a5fa" }}>{cameraStatus}</span>
        </p>
      </div>
    </div>
  );
}
