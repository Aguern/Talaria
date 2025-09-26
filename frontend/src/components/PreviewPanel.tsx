"use client";

import React from "react";
import { Document, Page, pdfjs } from "react-pdf";

// Fonction pour charger les CSS dynamiquement
const loadPDFStyles = () => {
  // Vérifier si les styles sont déjà chargés
  if (document.querySelector('link[href="/TextLayer.css"]')) return;
  
  const textLayerLink = document.createElement('link');
  textLayerLink.rel = 'stylesheet';
  textLayerLink.href = '/TextLayer.css';
  document.head.appendChild(textLayerLink);
  
  const annotationLayerLink = document.createElement('link');
  annotationLayerLink.rel = 'stylesheet';
  annotationLayerLink.href = '/AnnotationLayer.css';
  document.head.appendChild(annotationLayerLink);
};
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Alert, AlertDescription } from "@/components/ui/alert";
import {
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  RotateCw,
  Download,
  ExternalLink,
  Loader2,
  AlertCircle,
  FileText,
} from "lucide-react";
import { usePreview, useAuth } from "@/lib/stores";
import { isPdfFile, cn } from "@/lib/utils";
import { toast } from "sonner";

// Configure PDF.js worker (self-hosted for CSP compliance) - client side only
if (typeof window !== "undefined") {
  pdfjs.GlobalWorkerOptions.workerSrc = "/pdf.worker.min.js";
}

interface PreviewPanelProps {
  className?: string;
}

export function PreviewPanel({ className }: PreviewPanelProps) {
  const { isOpen, docUrl, docTitle, initialPage, highlightText, close } = usePreview();

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 bg-black/90 flex items-center justify-center" onClick={close}>
      {/* Modal */}
      <div 
        className={cn(
          "relative w-[80vw] h-[85vh] max-w-4xl bg-white dark:bg-gray-900 border rounded-lg shadow-2xl overflow-hidden flex flex-col",
          className
        )}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <div className="flex items-center space-x-2">
            <FileText className="h-5 w-5" />
            <div>
              <h2 className="font-semibold text-foreground truncate">{docTitle || "Aperçu du document"}</h2>
              <p className="text-sm text-muted-foreground">Aperçu et navigation dans le document</p>
            </div>
          </div>
          <Button variant="ghost" size="sm" onClick={close}>
            ×
          </Button>
        </div>

        <div className="flex-1 overflow-auto bg-gray-50 dark:bg-gray-800">
          {docUrl ? (
            (() => {
              console.log('PreviewPanel - docUrl:', docUrl);
              console.log('PreviewPanel - isPDF:', isPdfFile(docUrl));
              return isPdfFile(docUrl) ? (
                <PDFViewer
                  url={docUrl}
                  initialPage={initialPage}
                  title={docTitle}
                  highlightText={highlightText}
                />
              ) : (
                <NonPDFViewer url={docUrl} title={docTitle} />
              );
            })()
          ) : (
            <div className="flex h-full items-center justify-center">
              <p className="text-muted-foreground">Aucun document à afficher</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

interface PDFViewerProps {
  url: string;
  initialPage?: number;
  title?: string;
  highlightText?: string;
}

function PDFViewer({ url, initialPage = 1, title, highlightText }: PDFViewerProps) {
  const { token, currentTenant } = useAuth();
  const [numPages, setNumPages] = React.useState<number | null>(null);
  const [pageNumber, setPageNumber] = React.useState(1); // Toujours commencer à 1
  const [scale, setScale] = React.useState(1.0); // Taille normale
  const [rotation, setRotation] = React.useState(0);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);
  const containerRef = React.useRef<HTMLDivElement>(null);
  const targetPageRef = React.useRef<number>(initialPage); // Stocker la page cible

  // Mettre à jour la référence quand initialPage change
  React.useEffect(() => {
    targetPageRef.current = initialPage;
    console.log('PDFViewer - Target page updated to:', initialPage);
  }, [initialPage]);

  // Charger les styles PDF.js
  React.useEffect(() => {
    loadPDFStyles();
  }, []);

  // Fonction pour créer un renderer de texte personnalisé avec surlignage
  const customTextRenderer = React.useCallback(
    (textItem: any) => {
      if (!highlightText || !textItem.str) return textItem.str;

      // Prendre les premiers mots significatifs de l'excerpt (au moins 20 caractères)
      let searchText = highlightText.substring(0, 100).trim();
      
      // Nettoyer le texte (enlever les sauts de ligne, espaces multiples)
      searchText = searchText.replace(/\n/g, ' ').replace(/\s+/g, ' ');
      
      // Essayer de trouver des mots clés dans le texte
      const words = searchText.split(' ').filter(w => w.length > 3);
      const significantWords = words.slice(0, 5); // Prendre les 5 premiers mots significatifs
      
      // Créer un pattern de recherche flexible
      const pattern = significantWords.map(word => 
        word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&') // Échapper les caractères spéciaux
      ).join('|');
      
      if (!pattern) return textItem.str;

      try {
        const regex = new RegExp(`(${pattern})`, 'gi');
        const parts = textItem.str.split(regex);
        
        if (parts.length > 1) {
          return (
            <>
              {parts.map((part: string, index: number) => {
                // Vérifier si cette partie correspond à un mot recherché
                if (significantWords.some(word => 
                  part.toLowerCase() === word.toLowerCase()
                )) {
                  return (
                    <mark
                      key={index}
                      style={{
                        backgroundColor: '#2EE8B7',
                        padding: '0 2px',
                        color: '#0E4A67',
                        fontWeight: 'bold',
                        borderRadius: '2px',
                      }}
                    >
                      {part}
                    </mark>
                  );
                }
                return part;
              })}
            </>
          );
        }
      } catch (e) {
        console.error('Error in text highlighting:', e);
      }

      return textItem.str;
    },
    [highlightText]
  );

  // Navigation par scroll
  React.useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    const handleWheel = (e: WheelEvent) => {
      if (e.ctrlKey || e.metaKey) {
        // Zoom avec Ctrl/Cmd + scroll
        e.preventDefault();
        if (e.deltaY < 0) {
          zoomIn();
        } else {
          zoomOut();
        }
      } else if (Math.abs(e.deltaY) > Math.abs(e.deltaX)) {
        // Scroll vertical -> navigation pages
        if (e.deltaY > 50 && pageNumber < (numPages || 1)) {
          e.preventDefault();
          setPageNumber(prev => Math.min(numPages || 1, prev + 1));
        } else if (e.deltaY < -50 && pageNumber > 1) {
          e.preventDefault();
          setPageNumber(prev => Math.max(1, prev - 1));
        }
      }
    };

    container.addEventListener('wheel', handleWheel, { passive: false });
    return () => container.removeEventListener('wheel', handleWheel);
  }, [pageNumber, numPages]);

  const onDocumentLoadSuccess = ({ numPages }: { numPages: number }) => {
    setNumPages(numPages);
    setLoading(false);
    setError(null);
    
    // Naviguer vers la page cible après le chargement du document
    const targetPage = targetPageRef.current;
    if (targetPage && targetPage > 0 && targetPage <= numPages) {
      console.log(`Document loaded with ${numPages} pages, navigating to page ${targetPage}`);
      // Utiliser setTimeout pour s'assurer que le rendu est terminé
      setTimeout(() => {
        setPageNumber(targetPage);
      }, 100);
    } else {
      console.log(`Document loaded with ${numPages} pages, target page ${targetPage} is invalid`);
    }
  };

  const onDocumentLoadError = (error: Error) => {
    setError("Erreur lors du chargement du PDF");
    setLoading(false);
    console.error("PDF load error:", error);
  };

  const goToPrevPage = () => {
    setPageNumber(prev => Math.max(1, prev - 1));
  };

  const goToNextPage = () => {
    setPageNumber(prev => Math.min(numPages || 1, prev + 1));
  };

  const goToPage = (page: number) => {
    if (page >= 1 && page <= (numPages || 1)) {
      setPageNumber(page);
    }
  };

  const zoomIn = () => {
    setScale(prev => Math.min(3, prev + 0.2));
  };

  const zoomOut = () => {
    setScale(prev => Math.max(0.5, prev - 0.2));
  };

  const rotate = () => {
    setRotation(prev => (prev + 90) % 360);
  };

  const downloadPDF = () => {
    const link = document.createElement("a");
    link.href = url;
    link.download = title || "document.pdf";
    link.click();
  };

  const openExternal = () => {
    window.open(url, "_blank", "noopener,noreferrer");
  };

  // Configuration du fichier PDF avec authentification
  const pdfFileOptions = React.useMemo(() => {
    // Nettoyer l'URL en retirant le fragment #page=X pour l'authentification
    const cleanUrl = url.split('#')[0];
    return {
      url: cleanUrl,
      httpHeaders: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        ...(currentTenant ? { "X-Client-ID": currentTenant } : {}),
      },
    };
  }, [url, token, currentTenant]);

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>{error}</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* Alerte de surlignage */}
      {highlightText && (
        <Alert className="mx-3 mt-3 mb-2 bg-teal-50 border-teal-200">
          <AlertDescription className="text-sm">
            <span className="font-medium">🔍 Texte recherché :</span> Les mots clés de la citation sont surlignés en <span className="bg-teal-400 text-blue-900 px-1 rounded">vert</span>
          </AlertDescription>
        </Alert>
      )}
      
      {/* Controls simplifiés */}
      <div className="flex items-center justify-between border-b p-3">
        <div className="flex items-center space-x-3">
          <Button
            variant="outline"
            size="sm"
            onClick={goToPrevPage}
            disabled={pageNumber <= 1}
          >
            <ChevronLeft className="h-4 w-4" />
            Précédent
          </Button>
          
          <div className="flex items-center space-x-2">
            <span className="text-sm text-muted-foreground">Page</span>
            <Input
              type="number"
              value={pageNumber}
              onChange={(e) => goToPage(parseInt(e.target.value) || 1)}
              onFocus={(e) => e.target.select()}
              onClick={(e) => e.target.select()}
              className="w-16 h-8 text-center text-sm [&::-webkit-outer-spin-button]:appearance-none [&::-webkit-inner-spin-button]:appearance-none [-moz-appearance:textfield]"
              min={1}
              max={numPages || 1}
            />
            <span className="text-sm text-muted-foreground">sur {numPages || "?"}</span>
          </div>
          
          <Button
            variant="outline"
            size="sm"
            onClick={goToNextPage}
            disabled={pageNumber >= (numPages || 1)}
          >
            Suivant
            <ChevronRight className="h-4 w-4 ml-1" />
          </Button>
        </div>

        <div className="flex items-center space-x-2">
          <Button variant="outline" size="sm" onClick={zoomOut}>
            <ZoomOut className="h-4 w-4" />
          </Button>
          
          <Badge variant="outline" className="text-xs px-2">
            {Math.round(scale * 100)}%
          </Badge>
          
          <Button variant="outline" size="sm" onClick={zoomIn}>
            <ZoomIn className="h-4 w-4" />
          </Button>
          
          <span className="text-xs text-muted-foreground mx-2">•</span>
          
          <Button variant="outline" size="sm" onClick={downloadPDF}>
            <Download className="h-4 w-4" />
          </Button>
        </div>
      </div>

      {/* PDF Content */}
      <div 
        ref={containerRef}
        className="flex-1 overflow-auto flex items-center justify-center"
      >
        {loading && (
          <div className="flex h-full items-center justify-center">
            <div className="flex items-center space-x-2">
              <Loader2 className="h-6 w-6 animate-spin" />
              <span>Chargement du PDF...</span>
            </div>
          </div>
        )}

        <div className="p-2">
          <Document
            file={pdfFileOptions}
            onLoadSuccess={onDocumentLoadSuccess}
            onLoadError={onDocumentLoadError}
            loading=""
            error=""
          >
            <Page
              key={`page-${pageNumber}`}
              pageNumber={pageNumber}
              scale={scale}
              rotate={rotation}
              customTextRenderer={customTextRenderer}
              loading={
                <div className="flex h-[600px] w-[400px] items-center justify-center border border-dashed">
                  <Loader2 className="h-6 w-6 animate-spin" />
                </div>
              }
              error={
                <div className="flex h-[600px] w-[400px] items-center justify-center border border-dashed border-red-300 bg-red-50">
                  <div className="text-center">
                    <AlertCircle className="mx-auto h-8 w-8 text-red-500" />
                    <p className="mt-2 text-sm text-red-600">
                      Erreur de rendu de la page
                    </p>
                  </div>
                </div>
              }
            />
          </Document>
        </div>
      </div>
    </div>
  );
}

interface NonPDFViewerProps {
  url: string;
  title?: string;
}

function NonPDFViewer({ url, title }: NonPDFViewerProps) {
  const { token, currentTenant } = useAuth();
  const [blobUrl, setBlobUrl] = React.useState<string | null>(null);
  const [loading, setLoading] = React.useState(true);

  React.useEffect(() => {
    let revoke: string | null = null;
    (async () => {
      try {
        const res = await fetch(url, {
          headers: {
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
            ...(currentTenant ? { "X-Client-ID": currentTenant } : {}),
          },
        });
        if (!res.ok) throw new Error("Unauthorized");
        const blob = await res.blob();
        const objUrl = URL.createObjectURL(blob);
        setBlobUrl(objUrl);
        revoke = objUrl;
        setLoading(false);
      } catch (error) {
        console.error("Failed to load document:", error);
        setBlobUrl(null);
        setLoading(false);
      }
    })();
    return () => { 
      if (revoke) URL.revokeObjectURL(revoke); 
    };
  }, [url, token, currentTenant]);

  const openExternal = () => { 
    if (blobUrl) window.open(blobUrl, "_blank", "noopener,noreferrer"); 
  };

  const downloadFile = () => {
    if (!blobUrl) return;
    const link = document.createElement("a");
    link.href = blobUrl; 
    link.download = title || "document";
    link.click();
  };

  if (loading) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="flex items-center space-x-2">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span>Chargement du document...</span>
        </div>
      </div>
    );
  }

  if (!blobUrl) {
    return (
      <div className="flex h-full items-center justify-center">
        <div className="text-center space-y-2">
          <AlertCircle className="mx-auto h-8 w-8 text-red-500" />
          <p className="text-sm text-red-600">
            Erreur lors du chargement du document
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex h-full flex-col">
      {/* Controls */}
      <div className="flex items-center justify-between border-b p-2">
        <div className="flex items-center space-x-2">
          <FileText className="h-4 w-4" />
          <span className="text-sm font-medium">Document non-PDF</span>
        </div>

        <div className="flex items-center space-x-1">
          <Button variant="outline" size="sm" onClick={downloadFile}>
            <Download className="h-4 w-4 mr-1" />
            Télécharger
          </Button>
          
          <Button variant="outline" size="sm" onClick={openExternal}>
            <ExternalLink className="h-4 w-4 mr-1" />
            Ouvrir
          </Button>
        </div>
      </div>

      {/* Iframe */}
      <div className="flex-1 p-4">
        <iframe
          src={blobUrl}
          className="h-full w-full rounded border"
          sandbox="allow-same-origin allow-scripts"
          referrerPolicy="no-referrer"
          title={title}
          onError={() => {
            toast.error("Impossible d'afficher ce type de document");
          }}
        />
      </div>
    </div>
  );
}

// Hook for easier preview management
export function useDocumentPreview() {
  const { open, close, isOpen } = usePreview();

  const openDocument = (docId: string, options?: {
    page?: number;
    title?: string;
  }) => {
    const url = `/doc?id=${docId}${options?.page ? `#page=${options.page}` : ""}`;
    open({
      docUrl: url,
      docTitle: options?.title,
      initialPage: options?.page,
    });
  };

  return {
    openDocument,
    close,
    isOpen,
  };
}