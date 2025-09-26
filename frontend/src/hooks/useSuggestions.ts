import React from "react";
import { useQuery } from "@tanstack/react-query";
import { searchAPI } from "@/lib/api";
import { useDebounce } from "./useDebounce";

export function useSuggestions(query: string, enabled: boolean = true) {
  const debouncedQuery = useDebounce(query, 300);

  return useQuery({
    queryKey: ["suggestions", debouncedQuery],
    queryFn: () => searchAPI.getSuggestions(debouncedQuery, 5),
    enabled: enabled && debouncedQuery.length >= 2,
    staleTime: 60000, // Cache for 1 minute
    refetchOnWindowFocus: false,
  });
}

// Hook for debounce
export function useDebounce<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = React.useState<T>(value);

  React.useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(handler);
    };
  }, [value, delay]);

  return debouncedValue;
}