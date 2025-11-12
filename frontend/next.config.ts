// next.config.ts
import type { NextConfig } from "next";

const config: NextConfig = {
  // Configuration pour production Docker
  output: 'standalone',
  poweredByHeader: false,
  compress: true,

  // PAS de ignoreBuildErrors / ignoreDuringBuilds
  reactStrictMode: true,

  // Experimental features
  experimental: {
    // Configuration pour compatibilité
  },
  
  // Images configuration 
  images: {
    dangerouslyAllowSVG: true,
    unoptimized: true
  },
  
  // API Proxy vers le backend FastAPI
  async rewrites() {
    return [
      // Routes d'authentification (sans /api dans le backend)
      {
        source: '/api/token',
        destination: 'http://localhost:8000/token',
      },
      {
        source: '/api/users/:path*',
        destination: 'http://localhost:8000/users/:path*',
      },
      {
        source: '/api/users',
        destination: 'http://localhost:8000/users',
      },

      // Routes chat/MCP (avec /api dans le backend)
      {
        source: '/api/conversations/:path*',
        destination: 'http://localhost:8000/api/conversations/:path*',
      },
      {
        source: '/api/conversations',
        destination: 'http://localhost:8000/api/conversations',
      },
      {
        source: '/api/mcp/:path*',
        destination: 'http://localhost:8000/api/mcp/:path*',
      },
      {
        source: '/api/chat/:path*',
        destination: 'http://localhost:8000/api/chat/:path*',
      },
      {
        source: '/api/upload',
        destination: 'http://localhost:8000/api/upload',
      },

      // Routes des recettes
      {
        source: '/api/recipes',
        destination: 'http://localhost:8000/api/recipes/',
      },
      {
        source: '/api/recipes/:path+',
        destination: 'http://localhost:8000/api/recipes/:path*',
      },

      // Routes des packs
      {
        source: '/packs/:path*',
        destination: 'http://localhost:8000/packs/:path*',
      },

      // Autres routes
      {
        source: '/doc/:path*',
        destination: 'http://localhost:8000/doc/:path*',
      },
      {
        source: '/feedback',
        destination: 'http://localhost:8000/feedback',
      },
    ];
  },
  // Security headers for production
  // In development, headers are disabled to allow HMR and fast refresh
  headers: async () => {
    const isDevelopment = process.env.NODE_ENV === 'development';
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

    if (isDevelopment) {
      return []; // No CSP in development for HMR compatibility
    }

    // Production CSP - Note: 'unsafe-inline' is required for Next.js hydration
    // For stricter security, consider implementing nonce-based CSP
    const cspDirectives = [
      "default-src 'self'",
      "script-src 'self' 'unsafe-inline'", // Next.js requires unsafe-inline for hydration
      "style-src 'self' 'unsafe-inline'",  // Required for styled-components/CSS-in-JS
      "img-src 'self' blob: data: https:",
      "font-src 'self' data:",
      `connect-src 'self' ${apiUrl} ws: wss:`, // Allow API and WebSocket connections
      "frame-src 'self'",
      "frame-ancestors 'self'",
      "object-src 'none'",
      "base-uri 'self'",
      "form-action 'self'",
      "upgrade-insecure-requests"
    ].join("; ");

    return [
      {
        source: "/:path*",
        headers: [
          { key: "Content-Security-Policy", value: cspDirectives },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "SAMEORIGIN" },
          { key: "X-XSS-Protection", value: "1; mode=block" },
          { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
        ],
      },
    ];
  },
};

export default config;