"use client";

import React from "react";
import { useRouter } from "next/navigation";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { 
  Search, 
  Star, 
  Trash2, 
  RotateCcw, 
  Clock,
  Filter,
  X
} from "lucide-react";
import { useAuth } from "@/hooks/useAuth";
import { useHistory } from "@/lib/stores";
import dynamic from "next/dynamic";
import { CompactCitations } from "@/components/Citations";
import { formatDateShort, truncateText, escapeHtml } from "@/lib/utils";

// Import PreviewPanel dynamically to avoid SSR issues with PDF.js
const PreviewPanel = dynamic(() => import("@/components/PreviewPanel").then((mod) => ({ default: mod.PreviewPanel })), {
  ssr: false,
});
import { toast } from "sonner";
import type { SearchHistoryItem } from "@/lib/types";

export default function HistoryPage() {
  const router = useRouter();
  const auth = useAuth();
  const { items, favorites, toggleFavorite, removeItem, clearHistory } = useHistory();
  
  const [searchQuery, setSearchQuery] = React.useState("");
  const [filterFavorites, setFilterFavorites] = React.useState(false);

  // Redirect if not authenticated
  React.useEffect(() => {
    if (!auth.isAuthenticated) {
      router.push("/login");
    }
  }, [auth.isAuthenticated, router]);

  // Filter items based on search and favorites
  const filteredItems = React.useMemo(() => {
    let filtered = items;

    if (filterFavorites) {
      filtered = filtered.filter(item => item.isFavorite);
    }

    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      filtered = filtered.filter(item => 
        item.question.toLowerCase().includes(query) ||
        item.answer.toLowerCase().includes(query)
      );
    }

    return filtered;
  }, [items, searchQuery, filterFavorites]);

  // Sort items by date (newest first)
  const sortedItems = React.useMemo(() => {
    return [...filteredItems].sort((a, b) => (
      new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    ));
  }, [filteredItems]);

  // Pagination (optional)
  const [page, setPage] = React.useState(1);
  const PAGE_SIZE = 20;
  const pagedItems = React.useMemo(
    () => sortedItems.slice((page-1)*PAGE_SIZE, page*PAGE_SIZE),
    [sortedItems, page]
  );
  const totalPages = Math.ceil(sortedItems.length / PAGE_SIZE);

  const handleRerun = (item: SearchHistoryItem) => {
    // Navigate to search page and trigger search
    router.push(`/search?q=${encodeURIComponent(item.question)}`);
  };

  const handleRemove = (id: string) => {
    removeItem(id);
    toast.success("Élément supprimé de l'historique");
  };

  const handleToggleFavorite = (id: string) => {
    toggleFavorite(id);
    const item = items.find(i => i.id === id);
    if (item) {
      toast.success(
        item.isFavorite ? "Retiré des favoris" : "Ajouté aux favoris"
      );
    }
  };

  const handleClearAll = () => {
    if (window.confirm("Êtes-vous sûr de vouloir effacer tout l'historique ?")) {
      clearHistory();
      toast.success("Historique effacé");
    }
  };

  if (!auth.isAuthenticated) {
    return null; // Will redirect
  }

  return (
    <div className="container mx-auto p-6 max-w-4xl">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">Historique des recherches</h1>
            <p className="text-muted-foreground">
              Retrouvez et relancez vos recherches précédentes
            </p>
          </div>
          
          {items.length > 0 && (
            <Button
              variant="outline"
              onClick={handleClearAll}
              className="text-destructive hover:text-destructive"
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Tout effacer
            </Button>
          )}
        </div>

        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">{items.length}</div>
              <p className="text-sm text-muted-foreground">
                Recherches totales
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">{favorites.length}</div>
              <p className="text-sm text-muted-foreground">
                Favoris
              </p>
            </CardContent>
          </Card>
          
          <Card>
            <CardContent className="pt-6">
              <div className="text-2xl font-bold">
                {items.filter(i => 
                  new Date(i.timestamp) > new Date(Date.now() - 7 * 24 * 60 * 60 * 1000)
                ).length}
              </div>
              <p className="text-sm text-muted-foreground">
                Cette semaine
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Filters */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex flex-col sm:flex-row gap-4">
              <div className="relative flex-1">
                <Search className="absolute left-3 top-3 h-4 w-4 text-muted-foreground" />
                <Input
                  placeholder="Rechercher dans l'historique..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="pl-10"
                />
                {searchQuery && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setSearchQuery("")}
                    className="absolute right-1 top-1 h-8 w-8 p-0"
                  >
                    <X className="h-4 w-4" />
                  </Button>
                )}
              </div>
              
              <Button
                variant={filterFavorites ? "default" : "outline"}
                onClick={() => setFilterFavorites(!filterFavorites)}
                className="shrink-0"
              >
                <Star className={`mr-2 h-4 w-4 ${filterFavorites ? "fill-current" : ""}`} />
                Favoris uniquement
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Results */}
        {sortedItems.length === 0 ? (
          <Card>
            <CardContent className="pt-6">
              <div className="text-center space-y-4">
                <Clock className="mx-auto h-12 w-12 text-muted-foreground" />
                <div>
                  <h3 className="text-lg font-medium">
                    {items.length === 0 ? "Aucun historique" : "Aucun résultat"}
                  </h3>
                  <p className="text-muted-foreground">
                    {items.length === 0 
                      ? "Vos recherches apparaîtront ici"
                      : "Essayez d'ajuster vos filtres"
                    }
                  </p>
                </div>
                {items.length === 0 && (
                  <Button onClick={() => router.push("/search")}>
                    Commencer une recherche
                  </Button>
                )}
              </div>
            </CardContent>
          </Card>
        ) : (
          <div className="space-y-4">
            {pagedItems.map((item) => (
              <HistoryItemCard
                key={item.id}
                item={item}
                onRerun={() => handleRerun(item)}
                onToggleFavorite={() => handleToggleFavorite(item.id)}
                onRemove={() => handleRemove(item.id)}
              />
            ))}
            
            {/* Pagination */}
            {totalPages > 1 && (
              <div className="flex items-center justify-center space-x-4 pt-4">
                <Button
                  variant="outline"
                  onClick={() => setPage(page - 1)}
                  disabled={page <= 1}
                >
                  Précédent
                </Button>
                <span className="text-sm text-muted-foreground">
                  Page {page} sur {totalPages}
                </span>
                <Button
                  variant="outline"
                  onClick={() => setPage(page + 1)}
                  disabled={page >= totalPages}
                >
                  Suivant
                </Button>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Preview panel */}
      <PreviewPanel />
    </div>
  );
}

interface HistoryItemCardProps {
  item: SearchHistoryItem;
  onRerun: () => void;
  onToggleFavorite: () => void;
  onRemove: () => void;
}

function HistoryItemCard({ 
  item, 
  onRerun, 
  onToggleFavorite, 
  onRemove 
}: HistoryItemCardProps) {
  const [expanded, setExpanded] = React.useState(false);

  return (
    <Card className="transition-shadow hover:shadow-md">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="space-y-1 flex-1">
            <CardTitle className="text-base leading-relaxed">
              {item.question}
            </CardTitle>
            
            <div className="flex items-center space-x-2 text-sm text-muted-foreground">
              <Clock className="h-3 w-3" />
              <span>{formatDateShort(item.timestamp)}</span>
              
              {item.timing_ms && (
                <>
                  <span>•</span>
                  <span>{Math.round(item.timing_ms)}ms</span>
                </>
              )}
              
              {item.citations.length > 0 && (
                <>
                  <span>•</span>
                  <span>{item.citations.length} source{item.citations.length > 1 ? 's' : ''}</span>
                </>
              )}
            </div>
          </div>

          <div className="flex items-center space-x-1 ml-4">
            <Button
              variant="ghost"
              size="sm"
              onClick={onToggleFavorite}
              className="h-8 w-8 p-0"
              title={item.isFavorite ? "Retirer des favoris" : "Ajouter aux favoris"}
              aria-label={item.isFavorite ? "Retirer des favoris" : "Ajouter aux favoris"}
            >
              <Star className={`h-4 w-4 ${item.isFavorite ? "fill-current text-yellow-500" : ""}`} />
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={onRerun}
              className="h-8 w-8 p-0"
              title="Relancer la recherche"
              aria-label="Relancer la recherche"
            >
              <RotateCcw className="h-4 w-4" />
            </Button>
            
            <Button
              variant="ghost"
              size="sm"
              onClick={onRemove}
              className="h-8 w-8 p-0 text-destructive hover:text-destructive"
              title="Supprimer"
              aria-label="Supprimer"
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-0 space-y-3">
        {/* Answer preview */}
        <div className="bg-muted rounded-md p-3">
          <p className="text-sm whitespace-pre-wrap leading-6">
            {expanded ? item.answer : truncateText(item.answer, 200)}
          </p>

          {item.answer.length > 200 && (
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setExpanded(!expanded)}
              className="mt-2 h-6 p-0 text-xs"
              aria-expanded={expanded}
            >
              {expanded ? "Voir moins" : "Voir plus"}
            </Button>
          )}
        </div>

        {/* Citations */}
        {item.citations.length > 0 && (
          <div>
            <div className="text-sm font-medium mb-2">Sources :</div>
            <CompactCitations citations={item.citations} />
          </div>
        )}

        {/* Filters applied */}
        {Object.keys(item.filters).length > 0 && (
          <div>
            <div className="text-sm font-medium mb-2">Filtres appliqués :</div>
            <div className="flex flex-wrap gap-1">
              {Object.entries(item.filters).map(([key, value]) => (
                <Badge key={key} variant="outline" className="text-xs">
                  {key}: {String(value)}
                </Badge>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}