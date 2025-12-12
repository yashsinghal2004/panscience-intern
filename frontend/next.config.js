/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  // Ensure proper handling of client-side only modules
  experimental: {
    esmExternals: true,
  },
}

module.exports = nextConfig
