/** @type {import('next').NextConfig} */
const nextConfig = {
    output: 'standalone',
    env: {
        NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8080',
    },
    async rewrites() {
        return [
            {
                source: '/api/:path*',
                destination: 'http://iris-api-gateway:8080/v1/:path*',
            },
        ]
    },
}

module.exports = nextConfig
