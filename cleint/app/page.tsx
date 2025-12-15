"use client";

import { useState } from "react";

export default function Home() {
  const [status, setStatus] = useState<"idle" | "running" | "success" | "error">("idle");
  const [message, setMessage] = useState("Waiting...");

  const [form, setForm] = useState({
    fullName: "Anurag",
    mobileNumber: "9302919931",
    guardianMobileNumber: "7000175017",
    nearestCenter: "Raigarh Vidyapeeth (Pathshala Centre)",
    currentClass: "12th",
    offeredCourses: "One Year Classroom Program for JEE",
    schoolName: "o p jindal school",
    pincode: "496001",
    dateOfBirth: "11/07/2005",
  });

  async function handleApply() {
    setStatus("running");
    setMessage("Starting workflow…");

    try {
      const res = await fetch("/api/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(form),
      });
      const data = await res.json().catch(() => ({}));

      if (!res.ok || !data?.success) {
        const errText = typeof data?.error === "string" ? data.error : JSON.stringify(data?.error ?? data, null, 2);
        setStatus("error");
        setMessage(`Apply failed\n\n${errText}`);
        return;
      }

      setStatus("success");
      setMessage("Successfully applied");
    } catch (e) {
      const err = e as Error;
      setStatus("error");
      setMessage(`Apply failed\n\n${err?.message ?? String(e)}`);
    }
  }

  const statusColor = {
    idle: "bg-zinc-100 text-zinc-700 border-zinc-300",
    running: "bg-yellow-100 text-yellow-800 border-yellow-300",
    success: "bg-green-100 text-green-800 border-green-300",
    error: "bg-red-100 text-red-800 border-red-300",
  }[status];

  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black p-4">
      <main className="w-full max-w-lg bg-white dark:bg-black rounded-2xl border border-zinc-200 dark:border-zinc-800 p-8 shadow-lg">
        <h1 className="text-2xl font-semibold text-zinc-900 dark:text-zinc-50 mb-2">Student Admission — Apply</h1>
        <p className="text-zinc-600 dark:text-zinc-400 mb-6">Edit the details below, then click Apply to start the automation.</p>

        <div className="space-y-4">
          <input
            className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-700 rounded-lg bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-purple-500"
            placeholder="Full Name"
            value={form.fullName}
            onChange={(e) => setForm((f) => ({ ...f, fullName: e.target.value }))}
          />
          <input
            className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-700 rounded-lg bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-purple-500"
            placeholder="Mobile Number"
            value={form.mobileNumber}
            onChange={(e) => setForm((f) => ({ ...f, mobileNumber: e.target.value }))}
          />
          <input
            className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-700 rounded-lg bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-purple-500"
            placeholder="Guardian Mobile Number"
            value={form.guardianMobileNumber}
            onChange={(e) => setForm((f) => ({ ...f, guardianMobileNumber: e.target.value }))}
          />
          <input
            className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-700 rounded-lg bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-purple-500"
            placeholder="Nearest Center"
            value={form.nearestCenter}
            onChange={(e) => setForm((f) => ({ ...f, nearestCenter: e.target.value }))}
          />
          <input
            className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-700 rounded-lg bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-purple-500"
            placeholder="Current Class"
            value={form.currentClass}
            onChange={(e) => setForm((f) => ({ ...f, currentClass: e.target.value }))}
          />
          <input
            className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-700 rounded-lg bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-purple-500"
            placeholder="Offered Courses"
            value={form.offeredCourses}
            onChange={(e) => setForm((f) => ({ ...f, offeredCourses: e.target.value }))}
          />
          <input
            className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-700 rounded-lg bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-purple-500"
            placeholder="School Name"
            value={form.schoolName}
            onChange={(e) => setForm((f) => ({ ...f, schoolName: e.target.value }))}
          />
          <input
            className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-700 rounded-lg bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-purple-500"
            placeholder="Pincode"
            value={form.pincode}
            onChange={(e) => setForm((f) => ({ ...f, pincode: e.target.value }))}
          />
          <input
            className="w-full px-3 py-2 border border-zinc-300 dark:border-zinc-700 rounded-lg bg-white dark:bg-zinc-900 text-zinc-900 dark:text-zinc-100 focus:outline-none focus:ring-2 focus:ring-purple-500"
            placeholder="Date of Birth (MM/DD/YYYY)"
            value={form.dateOfBirth}
            onChange={(e) => setForm((f) => ({ ...f, dateOfBirth: e.target.value }))}
          />
        </div>

        <button
          onClick={handleApply}
          disabled={status === "running"}
          className="w-full mt-6 py-3 px-4 rounded-xl font-semibold bg-gradient-to-r from-purple-600 to-cyan-600 text-white hover:from-purple-700 hover:to-cyan-700 disabled:opacity-80 disabled:cursor-not-allowed transition-all"
        >
          {status === "running" ? "Applying…" : "Apply"}
        </button>

        <div className={`mt-4 p-3 rounded-lg border text-sm whitespace-pre-wrap ${statusColor}`}>
          {message}
        </div>

        <div className="mt-4 text-xs text-zinc-500 dark:text-zinc-500">
          Endpoint: <code className="text-zinc-700 dark:text-zinc-400">POST /api/start</code>
        </div>
      </main>
    </div>
  );
}
