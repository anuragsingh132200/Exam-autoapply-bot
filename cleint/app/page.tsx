"use client";

import { useState, useRef } from "react";

export default function Home() {
  const wsRef = useRef<WebSocket | null>(null);

  const [logs, setLogs] = useState<string[]>([]);
  const [status, setStatus] = useState<"idle" | "running" | "success" | "error">("idle");

  const [form] = useState({
    fullName: "Anurag",
    mobileNumber: "9302919931",
    guardianMobileNumber: "7000175017",
    mailId: "anurag132200@gmail.com",
    nearestCenter: "Raigarh Vidyapeeth",
    currentClass: "12th",
    offeredCourses: "JEE Program",
    schoolName: "OP Jindal School",
    pincode: "496001",
    dateOfBirth: "11/07/2005",
  });

  function handleApply() {
    setLogs(prevLogs => [...prevLogs, "Starting form submission..."]);
    setStatus("running");
    
    // Create a new WebSocket connection
    const ws = new WebSocket("ws://localhost:3000");
    wsRef.current = ws;

    ws.onopen = () => {
      setLogs(prevLogs => [...prevLogs, "Connected to server"]);
      
      // Send the form data with a specific message type
      const message = {
        type: "FORM_SUBMIT",
        payload: form
      };
      
      ws.send(JSON.stringify(message));
      setLogs(prevLogs => [...prevLogs, "Form data sent to server"]);
    };

    ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        console.log('Received message:', msg);

        switch (msg.type) {
          case 'LOG':
            setLogs(prevLogs => [...prevLogs, msg.message]);
            break;
            
          case 'SUBMISSION_RESULT':
            if (msg.payload.success) {
              setStatus("success");
              setLogs(prevLogs => [...prevLogs, "Form submitted successfully!"]);
            } else {
              setStatus("error");
              setLogs(prevLogs => [...prevLogs, `Error: ${msg.payload.message}`]);
            }
            // Close the connection after a short delay
            setTimeout(() => ws.close(), 1000);
            break;
            
          case 'ERROR':
            setStatus("error");
            setLogs(prevLogs => [...prevLogs, `Error: ${msg.payload?.message || 'Unknown error'}`]);
            ws.close();
            break;
            
          default:
            console.warn('Unknown message type:', msg.type);
        }
      } catch (error) {
        console.error('Error processing message:', error);
        setStatus("error");
        setLogs(prevLogs => [...prevLogs, 'Error processing server response']);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      setStatus("error");
      setLogs(prevLogs => [...prevLogs, 'Connection error. Please try again.']);
    };

    ws.onclose = () => {
      setLogs(prevLogs => [...prevLogs, "Connection closed"]);
      wsRef.current = null;
    };
  }

  return (
    <main className="p-10 max-w-xl mx-auto">
      <h1 className="text-2xl font-bold mb-4">Student Admission</h1>

      <button
        onClick={handleApply}
        disabled={status === "running"}
        className="px-4 py-2 bg-purple-600 text-white rounded"
      >
        {status === "running" ? "Applying…" : "Apply"}
      </button>

      <div className="mt-6 p-4 border rounded text-sm whitespace-pre-wrap">
        {logs.join("\n")}
      </div>
    </main>
  );
}
