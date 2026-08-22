import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  allowedDevOrigins: ['192.168.137.93', '10.34.129.209', '10.70.76.2'],
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8000/api/:path*',
      },
      {
        source: '/ws',
        destination: 'http://127.0.0.1:8000/ws',
      }
    ]
  },
};

export default nextConfig;
