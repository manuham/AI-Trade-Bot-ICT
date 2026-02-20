"use client";

import { useState } from "react";

export default function WaitlistForm() {
  const [email, setEmail] = useState("");
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle");
  const [message, setMessage] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!email) return;

    setStatus("loading");
    try {
      const res = await fetch("/api/waitlist", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });
      const data = await res.json();

      if (res.ok) {
        setStatus("success");
        setMessage(data.message || "You're on the list!");
        setEmail("");
      } else {
        setStatus("error");
        setMessage(data.error || "Something went wrong.");
      }
    } catch {
      setStatus("error");
      setMessage("Network error — please try again.");
    }
  }

  return (
    <div id="waitlist" className="scroll-mt-24">
      <form
        onSubmit={handleSubmit}
        className="flex flex-col sm:flex-row gap-3 max-w-md mx-auto"
      >
        <input
          type="email"
          placeholder="your@email.com"
          value={email}
          onChange={(e) => {
            setEmail(e.target.value);
            if (status !== "idle") setStatus("idle");
          }}
          required
          className="flex-1 px-4 py-3 rounded-xl border border-border bg-bg-primary text-text-primary text-sm outline-none focus:border-accent transition-colors duration-200 placeholder:text-text-muted"
        />
        <button
          type="submit"
          disabled={status === "loading"}
          className="px-6 py-3 rounded-xl border-none bg-accent hover:bg-accent-hover text-white font-semibold text-sm cursor-pointer transition-all duration-200 disabled:opacity-60 disabled:cursor-wait glow-accent whitespace-nowrap"
        >
          {status === "loading" ? (
            <span className="inline-flex items-center gap-2">
              <span className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
              Joining...
            </span>
          ) : (
            "Join Waitlist"
          )}
        </button>
      </form>

      {/* Status messages */}
      {status === "success" && (
        <p className="text-center text-green text-sm mt-3 animate-fade-in-up">
          {message}
        </p>
      )}
      {status === "error" && (
        <p className="text-center text-red text-sm mt-3 animate-fade-in-up">
          {message}
        </p>
      )}
    </div>
  );
}
