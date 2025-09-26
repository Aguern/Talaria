// next.config.ts
import type { NextConfig } from "next";

const config: NextConfig = {
  // Configuration pour production Docker
  output: 'standalone',
  poweredByHeader: false,
  compress: true,
  
  // PAS de ignoreBuildErrors / ignoreDuringBuilds
  reactStrictMode: true,
  
  // Images configuration 
  images: {
    dangerouslyAllowSVG: true,
    unoptimized: true
  },
  
  // API Proxy vers le backend FastAPI
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/:path*',
      },
      {
        source: '/doc/:path*',
        destination: 'http://localhost:8000/doc/:path*',
      },
      {
        source: '/feedback',
        destination: 'http://localhost:8000/feedback',
      },
      {
        source: '/packs/:path*',
        destination: 'http://localhost:8000/packs/:path*',
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