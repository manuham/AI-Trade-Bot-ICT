import { NextRequest, NextResponse } from "next/server";

// In-memory store as fallback for Vercel serverless (no filesystem persistence)
// For production, replace with a real database (Supabase, PlanetScale, etc.)
// or use an email service API (Mailchimp, Resend, ConvertKit)
let memoryWaitlist: { email: string; joined_at: string }[] = [];

// Try filesystem storage (works locally and on VPS, NOT on Vercel)
async function getWaitlistFromFile(): Promise<{ email: string; joined_at: string }[]> {
  try {
    const { promises: fs } = await import("fs");
    const path = await import("path");
    const filePath = path.join(process.cwd(), "data", "waitlist.json");
    const raw = await fs.readFile(filePath, "utf-8");
    return JSON.parse(raw);
  } catch {
    return [];
  }
}

async function saveWaitlistToFile(entries: { email: string; joined_at: string }[]): Promise<boolean> {
  try {
    const { promises: fs } = await import("fs");
    const path = await import("path");
    const dataDir = path.join(process.cwd(), "data");
    await fs.mkdir(dataDir, { recursive: true });
    await fs.writeFile(
      path.join(dataDir, "waitlist.json"),
      JSON.stringify(entries, null, 2)
    );
    return true;
  } catch {
    return false;
  }
}

async function getWaitlist(): Promise<{ email: string; joined_at: string }[]> {
  // Try file first, fall back to memory
  const fileList = await getWaitlistFromFile();
  if (fileList.length > 0) return fileList;
  return memoryWaitlist;
}

async function addToWaitlist(email: string): Promise<{ success: boolean; position: number; alreadyExists: boolean }> {
  const waitlist = await getWaitlist();

  // Check duplicate
  if (waitlist.some((e) => e.email === email)) {
    return { success: true, position: 0, alreadyExists: true };
  }

  const entry = { email, joined_at: new Date().toISOString() };
  waitlist.push(entry);

  // Try to save to file, fall back to memory
  const fileSaved = await saveWaitlistToFile(waitlist);
  if (!fileSaved) {
    memoryWaitlist = waitlist;
  }

  return { success: true, position: waitlist.length, alreadyExists: false };
}

export async function POST(req: NextRequest) {
  try {
    const body = await req.json();
    const email = body.email?.trim().toLowerCase();

    // Validate email
    if (!email || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return NextResponse.json(
        { error: "Please enter a valid email address." },
        { status: 400 }
      );
    }

    const result = await addToWaitlist(email);

    if (result.alreadyExists) {
      return NextResponse.json(
        { message: "You're already on the waitlist! We'll be in touch." },
        { status: 200 }
      );
    }

    return NextResponse.json(
      {
        message: "Welcome aboard! You'll be the first to know when we launch.",
        position: result.position,
      },
      { status: 201 }
    );
  } catch {
    return NextResponse.json(
      { error: "Server error — please try again later." },
      { status: 500 }
    );
  }
}

export async function GET() {
  const waitlist = await getWaitlist();
  return NextResponse.json({ count: waitlist.length });
}
