"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { 
  ExternalLink, 
  Copy, 
  Eye, 
  FileText, 
  AlertCircle,
  CheckCircle 
} from "lucide-react";
import { usePreview } from "@/lib/stores";
import { copyToClipboard, formatCitationText, truncateText, escapeHtml } from "@/lib/utils";
import { toast } from "sonner";
import type { Citation } from "@/lib/types";

interface CitationsProps {
  citations: Citation[];
  className?: string;
}

export function Citations({ citations, className }: CitationsProps) {
  if (!citations || citations.length === 0) {
    return (
      <Alert className={className}>
        <AlertCircle className="h-4 w-4" />
        <AlertDescription>
          Aucune citation trouvée pour cette réponse.
        </AlertDescription>
      </Alert>
    );
  }

  return (
    <div className={className} data-testid="citations-list">
      <div className="flex items-center space-x-3 mb-6">
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center">
          <FileText className="h-4 w-4 text-primary" />
        </div>
        <h3 className="text-2xl font-bold bg-gradient-to-r from-foreground to-muted-foreground bg-clip-text text-transparent">
          Sources documentaires ({citations.length})
        </h3>
      </div>
      
      <div className="grid gap-4">
        {citations.map((citation, index) => (
          <CitationCard
            key={`${citation.doc_id}-${citation.page || index}`}
            citation={citation}
            index={index + 1}
          />
        ))}
      </div>
    </div>
  );
}

interface CitationCardProps {
  citation: Citation;
  index: number;
}

function CitationCard({ citation, index }: CitationCardProps) {
  const { open: openPreview } = usePreview();

  const handlePreview = () => {
    const url = citation.url || `/doc?id=${citation.doc_id}${citation.page ? `#page=${citation.page}` : ""}`;
    const title = citation.file_name || `Document ${citation.doc_id}`;
    
    console.log('Citation handlePreview - citation:', citation);
    console.log('Citation handlePreview - page:', citation.page);
    console.log('Citation handlePreview - url:', url);
    console.log('Citation handlePreview - initialPage:', citation.page);
    console.log('Citation handlePreview - highlightText:', citation.excerpt);
    
    openPreview({
      docUrl: url,
      docTitle: title,
      initialPage: citation.page,
      highlightText: citation.excerpt,
    });
  };

  const handleCopy = async () => {
    const citationText = formatCitationText(citation);
    const success = await copyToClipboard(citationText);
    
    if (success) {
      toast.success("Citation copiée !", { duration: 2000 });
    } else {
      toast.error("Échec de la copie");
    }
  };

  const handleOpenExternal = () => {
    // Use preview panel for authenticated access instead of direct URL
    handlePreview();
  };

  return (
    <Card className="relative glass border-primary/10 card-hover backdrop-blur-xl" data-testid={`citation-card-${index}`}>
      <CardHeader className="pb-4">
        <div className="flex items-start justify-between">
          <div className="flex items-start space-x-4">
            {/* Citation number - Modern design */}
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-gradient-to-br from-primary/20 to-accent/20 text-sm font-bold text-primary border border-primary/20">
              {index}
            </div>
            
            <div className="space-y-3 flex-1">
              {/* File name - Enhanced typography */}
              <CardTitle className="text-lg font-semibold">
                <div className="flex items-center space-x-3">
                  <div className="flex items-center space-x-2">
                    <FileText className="h-5 w-5 text-primary" />
                    <span className="text-foreground">
                      {citation.file_name || `Document ${citation.doc_id}`}
                    </span>
                  </div>
                  {citation.page && (
                    <Badge variant="outline" className="glass border-primary/20 text-primary">
                      Page {citation.page}
                    </Badge>
                  )}
                </div>
              </CardTitle>
              
              {/* Metadata badges - Modern styling */}
              <div className="flex flex-wrap gap-2">
                {citation.source && (
                  <Badge variant="secondary" className="glass bg-secondary/50 text-secondary-foreground">
                    {citation.source}
                  </Badge>
                )}
                {citation.doc_type && (
                  <Badge variant="outline" className="glass border-muted-foreground/20">
                    {citation.doc_type}
                  </Badge>
                )}
              </div>
            </div>
          </div>

          {/* Action buttons - Modern glass design */}
          <div className="flex space-x-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handlePreview}
              className="h-10 w-10 p-0 glass border-primary/20 hover:border-primary/40 hover:bg-primary/10"
              title="Aperçu"
              data-testid={`preview-citation-${index}`}
            >
              <Eye className="h-4 w-4" />
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={handleCopy}
              className="h-10 w-10 p-0 glass border-accent/20 hover:border-accent/40 hover:bg-accent/10"
              title="Copier la citation"
              data-testid={`copy-citation-${index}`}
            >
              <Copy className="h-4 w-4" />
            </Button>
            
            <Button
              variant="outline"
              size="sm"
              onClick={handleOpenExternal}
              className="h-10 w-10 p-0 glass border-muted/20 hover:border-muted/40 hover:bg-muted/10"
              title="Ouvrir dans un nouvel onglet"
              data-testid={`open-citation-${index}`}
            >
              <ExternalLink className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>

      {/* Excerpt - Enhanced readability */}
      {citation.excerpt && (
        <CardContent className="pt-0">
          <div className="glass rounded-xl p-4 border border-muted/20 bg-muted/10">
            <p className="text-muted-foreground leading-relaxed italic">
              "{truncateText(citation.excerpt, 200)}"
            </p>
          </div>
        </CardContent>
      )}
    </Card>
  );
}

// Compact citations list for smaller spaces
interface CompactCitationsProps {
  citations: Citation[];
  maxVisible?: number;
  className?: string;
}

export function CompactCitations({ 
  citations, 
  maxVisible = 3,
  className 
}: CompactCitationsProps) {
  const [showAll, setShowAll] = React.useState(false);
  
  if (!citations || citations.length === 0) {
    return null;
  }

  const visibleCitations = showAll ? citations : citations.slice(0, maxVisible);
  const hasMore = citations.length > maxVisible;

  return (
    <div className={className} data-testid="compact-citations">
      <div className="flex flex-wrap gap-2">
        {visibleCitations.map((citation, index) => (
          <CompactCitationBadge
            key={`${citation.doc_id}-${citation.page || index}`}
            citation={citation}
            index={index + 1}
          />
        ))}
        
        {hasMore && !showAll && (
          <Button
            variant="outline"
            size="sm"
            onClick={() => setShowAll(true)}
            className="h-6 px-2 text-xs"
            data-testid="show-more-citations"
          >
            +{citations.length - maxVisible} autres
          </Button>
        )}
      </div>
    </div>
  );
}

interface CompactCitationBadgeProps {
  citation: Citation;
  index: number;
}

function CompactCitationBadge({ citation, index }: CompactCitationBadgeProps) {
  const { open: openPreview } = usePreview();

  const handleClick = () => {
    const url = citation.url || `/doc?id=${citation.doc_id}${citation.page ? `#page=${citation.page}` : ""}`;
    const title = citation.file_name || `Document ${citation.doc_id}`;
    
    openPreview({
      docUrl: url,
      docTitle: title,
      initialPage: citation.page,
    });
  };

  const displayText = citation.file_name || `Doc ${citation.doc_id}`;
  const pageText = citation.page ? ` p.${citation.page}` : "";

  return (
    <Badge
      variant="outline"
      className="cursor-pointer hover:bg-accent"
      onClick={handleClick}
      title={`${displayText}${pageText}`}
      data-testid={`compact-citation-badge-${index}`}
    >
      <span className="mr-1 text-xs">[{index}]</span>
      {truncateText(displayText, 20)}
      {pageText}
    </Badge>
  );
}

// Citation confidence indicator
interface CitationConfidenceProps {
  confidence?: number;
  className?: string;
}

export function CitationConfidence({ 
  confidence, 
  className 
}: CitationConfidenceProps) {
  if (confidence === undefined) return null;

  const getConfidenceData = (score: number) => {
    if (score >= 0.8) {
      return {
        label: "Très pertinent",
        color: "text-green-600",
        icon: CheckCircle,
        variant: "default" as const,
      };
    } else if (score >= 0.6) {
      return {
        label: "Pertinent",
        color: "text-yellow-600", 
        icon: AlertCircle,
        variant: "secondary" as const,
      };
    } else {
      return {
        label: "Peu pertinent",
        color: "text-red-600",
        icon: AlertCircle,
        variant: "destructive" as const,
      };
    }
  };

  const { label, color, icon: Icon, variant } = getConfidenceData(confidence);

  return (
    <div className={className} data-testid="citation-confidence">
      <Badge variant={variant} className="text-xs">
        <Icon className="mr-1 h-3 w-3" />
        {label} ({Math.round(confidence * 100)}%)
      </Badge>
    </div>
  );
}