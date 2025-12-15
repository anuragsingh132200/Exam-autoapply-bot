import { NextRequest, NextResponse } from "next/server";

export async function POST(req: NextRequest) {
  try {
    const body = await req.json().catch(() => ({}));

    const backendUrl = "http://localhost:3000/start";
    const res = await fetch(backendUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const response = await res.json().catch(() => ({}));

    return NextResponse.json(response, { status: res.status });
  } catch (e) {
    return NextResponse.json(
      { success: false, error: (e as Error)?.message ?? String(e) },
      { status: 500 }
    );
  }
}
