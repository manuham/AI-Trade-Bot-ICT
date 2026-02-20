import type { Metadata } from "next";
import { Analytics } from "@vercel/analytics/react";
import { SpeedInsights } from "@vercel/speed-insights/next";
import "./globals.css";

export const metadata: Metadata = {
  title: "AI Trade Bot ICT — AI-Powered Forex Signals",
  description:
    "Professional forex trade signals using Claude AI and ICT methodology. Full transparency — every trade shown, wins AND losses. Multi-pair analysis with 12-point checklist scoring.",
  keywords: [
    "forex signals",
    "ICT methodology",
    "AI trading",
    "forex bot",
    "Claude AI",
    "trade signals",
    "ICT trading",
    "order blocks",
    "fair value gaps",
    "smart money concepts",
  ],
  openGraph: {
    title: "AI Trade Bot ICT — AI-Powered Forex Signals",
    description:
      "Professional forex signals with verified track record. ICT methodology meets artificial intelligence. Every trade shown — full transparency.",
    type: "website",
    siteName: "AI Trade Bot ICT",
  },
  twitter: {
    card: "summary_large_image",
    title: "AI Trade Bot ICT — AI-Powered Forex Signals",
    description:
      "Professional forex signals with verified track record. Full transparency — every trade shown.",
  },
  robots: {
    index: true,
    follow: true,
  },
  metadataBase: new URL("https://icttradebot.com"),
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" className="scroll-smooth">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="antialiased bg-bg-primary text-text-primary">
        {children}
        <Analytics />
        <SpeedInsights />
      </body>
    </html>
  );
}
