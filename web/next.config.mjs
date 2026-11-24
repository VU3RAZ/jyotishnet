// SPDX-License-Identifier: AGPL-3.0-or-later
// The browser talks to /api/*; Next forwards it to the FastAPI service.
const API_URL = process.env.JYOTISHNET_API_URL || "http://127.0.0.1:8000";

/** @type {import('next').NextConfig} */
export default {
  reactStrictMode: true,
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API_URL}/:path*` }];
  },
};
