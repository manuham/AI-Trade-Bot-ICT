import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  experimental: {},

  // Proxy client-side API requests through Vercel to avoid mixed content (HTTPS→HTTP)
  // Browser hits https://icttradebot.com/api/vps/public/trades
  // Vercel server proxies to http://VPS:8000/public/trades
  async rewrites() {
    const backendUrl =
      process.env.BACKEND_URL || "http://46.225.66.110:8000";
    return [
      {
        source: "/api/vps/:path*",
        destination: `${backendUrl}/:path*`,
      },
    ];
  },
};

export default nextConfig;
