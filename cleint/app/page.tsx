"use client";

import { useState, useRef } from "react";

export default function Home() {
  const wsRef = useRef<WebSocket | null>(null);

  const [logs, setLogs] = useState<string[]>([]);
  const [status, setStatus] = useState("idle");
  const [otp, setOtp] = useState("");
  const [otpRequested, setOtpRequested] = useState(false);

  const form = {
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
  };

  const log = (m: string) =>
    setLogs((l) => [...l, m]);

  function handleApply() {
    const ws = new WebSocket("ws://localhost:3000");
    wsRef.current = ws;
    setStatus("running");

    ws.onopen = () => {
      log("Connected to server");
      ws.send(JSON.stringify({ type: "FORM_SUBMIT", payload: form }));
    };

    ws.onmessage = (e) => {
      const msg = JSON.parse(e.data);

      if (msg.type === "LOG") log(msg.payload ?? msg.message);
      if (msg.type === "REQUEST_OTP") {
        setOtpRequested(true);
        log("OTP requested");
      }
      if (msg.type === "SUBMISSION_RESULT") {
        setStatus(msg.payload.success ? "success" : "error");
        log("Workflow finished");
      }
    };
  }

  function submitOtp() {
    wsRef.current?.send(
      JSON.stringify({ type: "OTP_SUBMIT", payload: { otp } })
    );
    setOtpRequested(false);
    log("OTP sent to server");
  }

  return (
    <main className="p-8 max-w-xl mx-auto">
      <button
        onClick={handleApply}
        disabled={status === "running"}
        className="px-4 py-2 bg-purple-600 text-white rounded"
      >
        Apply
      </button>

      {otpRequested && (
        <div className="mt-4">
          <input
            value={otp}
            onChange={(e) => setOtp(e.target.value)}
            placeholder="Enter OTP"
            className="border px-2 py-1"
          />
          <button
            onClick={submitOtp}
            className="ml-2 px-3 py-1 bg-green-600 text-white rounded"
          >
            Submit OTP
          </button>
        </div>
      )}

      <pre className="mt-6 border p-4 text-sm">
        {logs.join("\n")}
      </pre>
    </main>
  );
}
