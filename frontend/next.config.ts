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
  // Si tu sers le PDF worker depuis /public :
  // (copie "node_modules/pdfjs-dist/build/pdf.worker.min.js" → "public/pdf.worker.min.js")
  // Désactivation temporaire du CSP pour développement
  headers: async () => 
    process.env.NODE_ENV === 'development' 
      ? [] // Pas de headers en développement
      : [
          {
            source: "/:path*",
            headers: [
              { key: "Content-Security-Policy", value: "default-src 'self'; img-src 'self' blob: data:; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; font-src 'self'; frame-ancestors 'self'; object-src 'none'; base-uri 'self';" },
              { key: "Referrer-Policy", value: "no-referrer" },
              { key: "X-Content-Type-Options", value: "nosniff" },
              { key: "X-Frame-Options", value: "SAMEORIGIN" },
            ],
          },
        ],
};

export default config;