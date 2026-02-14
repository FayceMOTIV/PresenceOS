const withPWA = require("@ducanh2912/next-pwa").default({
  dest: "public",
  register: true,
  skipWaiting: true,
  disable: process.env.NODE_ENV === "development",
  cacheOnFrontEndNav: true,
  reloadOnOnline: true,
  workboxOptions: {
    runtimeCaching: [
      {
        urlPattern: /^https?:\/\/.*\/api\/v1\/.*/i,
        handler: "NetworkFirst",
        options: {
          cacheName: "api-cache",
          expiration: {
            maxEntries: 64,
            maxAgeSeconds: 24 * 60 * 60,
          },
          networkTimeoutSeconds: 10,
        },
      },
      {
        urlPattern: /\.(?:png|jpg|jpeg|svg|gif|webp|avif)$/i,
        handler: "CacheFirst",
        options: {
          cacheName: "image-cache",
          expiration: {
            maxEntries: 128,
            maxAgeSeconds: 30 * 24 * 60 * 60,
          },
        },
      },
      {
        urlPattern: /\.(?:woff|woff2|ttf|otf)$/i,
        handler: "CacheFirst",
        options: {
          cacheName: "font-cache",
          expiration: {
            maxEntries: 32,
            maxAgeSeconds: 365 * 24 * 60 * 60,
          },
        },
      },
    ],
  },
});

const withBundleAnalyzer = require("@next/bundle-analyzer")({
  enabled: process.env.ANALYZE === "true",
});

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: "standalone",
  reactStrictMode: true,
  compress: true,
  poweredByHeader: false,
  generateEtags: true,

  images: {
    remotePatterns: [
      {
        protocol: "https",
        hostname: "**.cdninstagram.com",
      },
      {
        protocol: "https",
        hostname: "**.fbcdn.net",
      },
      {
        protocol: "https",
        hostname: "avatars.githubusercontent.com",
      },
      {
        protocol: "http",
        hostname: "localhost",
      },
    ],
    formats: ["image/avif", "image/webp"],
    minimumCacheTTL: 60,
  },

  async rewrites() {
    return [
      {
        source: "/api/v1/:path*",
        destination: `${process.env.NEXT_PUBLIC_API_URL}/api/v1/:path*`,
      },
    ];
  },

  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          {
            key: "X-DNS-Prefetch-Control",
            value: "on",
          },
          {
            key: "Strict-Transport-Security",
            value: "max-age=63072000; includeSubDomains; preload",
          },
          {
            key: "X-Frame-Options",
            value: "SAMEORIGIN",
          },
          {
            key: "X-Content-Type-Options",
            value: "nosniff",
          },
          {
            key: "Referrer-Policy",
            value: "origin-when-cross-origin",
          },
          {
            key: "Permissions-Policy",
            value: "camera=(), microphone=(self), geolocation=()",
          },
        ],
      },
    ];
  },
};

module.exports = withBundleAnalyzer(withPWA(nextConfig));
