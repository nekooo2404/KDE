/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  // Tự động proxy gọi /api sang Django Backend ở cổng 8000
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8000/api/:path*',
      },
    ]
  },
}

export default nextConfig
