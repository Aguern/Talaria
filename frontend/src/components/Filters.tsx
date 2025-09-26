"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Checkbox } from "@/components/ui/checkbox";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { RotateCcw, X, Settings } from "lucide-react";
import type { FilterSchema, FilterField } from "@/lib/types";
import { cn } from "@/lib/utils";

type FilterValue =
  | string
  | string[]
  | boolean
  | Record<string, string | null | undefined>
  | undefined;

interface FiltersProps {
  schema: FilterSchema;
  values: Record<string, FilterValue>;
  onChange: (id: string, value: FilterValue) => void;
  onReset: () => void;
  className?: string;
}

export function Filters({
  schema,
  values,
  onChange,
  onReset,
  className,
}: FiltersProps) {
  if (!schema.length) {
    return null;
  }

  const hasActiveFilters = Object.values(values).some(value => {
    if (Array.isArray(value)) return value.length > 0;
    if (typeof value === "object" && value !== null) {
      return Object.values(value).some(v => v !== null && v !== "");
    }
    return value !== "" && value !== null && value !== undefined;
  });

  return (
    <Card className={cn("glass border-primary/10 backdrop-blur-xl", className)} data-testid="filters-panel">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-xl font-semibold flex items-center space-x-2">
            <div className="w-6 h-6 rounded-lg bg-gradient-to-br from-primary/20 to-accent/20 flex items-center justify-center">
              <Settings className="h-3 w-3 text-primary" />
            </div>
            <span>Filtres intelligents</span>
          </CardTitle>
          {hasActiveFilters && (
            <Button
              variant="outline"
              size="sm"
              onClick={onReset}
              className="h-9 px-3 glass border-primary/20 hover:border-primary/40"
              data-testid="reset-filters"
            >
              <RotateCcw className="mr-2 h-4 w-4" />
              Reset
            </Button>
          )}
        </div>
      </CardHeader>
      
      <CardContent className="space-y-6">
        {schema.map((field) => (
          <FilterField
            key={field.id}
            field={field}
            value={values[field.id]}
            onChange={(value) => onChange(field.id, value)}
          />
        ))}
      </CardContent>
    </Card>
  );
}

interface FilterFieldProps {
  field: FilterField;
  value: FilterValue;
  onChange: (value: FilterValue) => void;
}

function FilterField({ field, value, onChange }: FilterFieldProps) {
  switch (field.type) {
    case "select":
      return (
        <div className="space-y-2">
          <Label htmlFor={field.id}>{field.label}</Label>
          <Select value={typeof value === "string" ? value : ""} onValueChange={onChange}>
            <SelectTrigger id={field.id} data-testid={`filter-select-${field.id}`}>
              <SelectValue placeholder={`Sélectionner ${field.label.toLowerCase()}`} />
            </SelectTrigger>
            <SelectContent>
              {field.options.map((option) => (
                <SelectItem key={option.value} value={option.value}>
                  {option.label}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      );

    case "text":
      return (
        <div className="space-y-2">
          <Label htmlFor={field.id}>{field.label}</Label>
          <Input
            id={field.id}
            type="text"
            value={typeof value === "string" ? value : ""}
            onChange={(e) => onChange(e.target.value)}
            placeholder={`Rechercher par ${field.label.toLowerCase()}`}
            data-testid={`filter-text-${field.id}`}
          />
        </div>
      );

    case "checkbox-group":
      return (
        <div className="space-y-2">
          <Label>{field.label}</Label>
          <div className="space-y-2">
            {field.options.map((option) => {
              const isChecked = Array.isArray(value) && value.includes(option.value);
              return (
                <div key={option.value} className="flex items-center space-x-2">
                  <Checkbox
                    id={`${field.id}-${option.value}`}
                    checked={isChecked}
                    onCheckedChange={(checked) => {
                      const currentValues = Array.isArray(value) ? value : [];
                      if (checked) {
                        onChange([...currentValues, option.value]);
                      } else {
                        onChange(currentValues.filter((v) => v !== option.value));
                      }
                    }}
                    data-testid={`filter-checkbox-${field.id}-${option.value}`}
                  />
                  <Label
                    htmlFor={`${field.id}-${option.value}`}
                    className="text-sm font-normal"
                  >
                    {option.label}
                  </Label>
                </div>
              );
            })}
          </div>
        </div>
      );

    case "chips":
      return (
        <div className="space-y-2">
          <Label>{field.label}</Label>
          <ChipsFilter
            options={field.options}
            value={Array.isArray(value) ? value : []}
            onChange={onChange}
            max={field.max}
          />
        </div>
      );

    case "date-range":
      return (
        <div className="space-y-2">
          <Label>{field.label}</Label>
          <div className="text-sm text-muted-foreground">
            Filtrage par dates (à implémenter)
          </div>
        </div>
      );

    default:
      return null;
  }
}

interface ChipsFilterProps {
  options: Array<{ value: string; label: string }>;
  value: string[];
  onChange: (value: string[]) => void;
  max?: number;
}

function ChipsFilter({ options, value, onChange, max }: ChipsFilterProps) {
  const handleToggle = (optionValue: string) => {
    const isSelected = value.includes(optionValue);
    
    if (isSelected) {
      onChange(value.filter((v) => v !== optionValue));
    } else {
      if (max && value.length >= max) {
        // Replace the first item if at max
        onChange([...value.slice(1), optionValue]);
      } else {
        onChange([...value, optionValue]);
      }
    }
  };

  return (
    <div className="space-y-3">
      {/* Selected chips */}
      {value.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {value.map((selectedValue) => {
            const option = options.find((opt) => opt.value === selectedValue);
            if (!option) return null;
            
            return (
              <Badge
                key={selectedValue}
                variant="default"
                className="cursor-pointer"
                onClick={() => handleToggle(selectedValue)}
                data-testid={`filter-chip-selected-${selectedValue}`}
              >
                {option.label}
                <X className="ml-1 h-3 w-3" />
              </Badge>
            );
          })}
        </div>
      )}

      {/* Available options */}
      <div className="flex flex-wrap gap-2">
        {options
          .filter((option) => !value.includes(option.value))
          .map((option) => (
            <Badge
              key={option.value}
              variant="outline"
              className="cursor-pointer hover:bg-accent"
              onClick={() => handleToggle(option.value)}
              data-testid={`filter-chip-available-${option.value}`}
            >
              {option.label}
            </Badge>
          ))}
      </div>

      {max && (
        <div className="text-xs text-muted-foreground">
          Maximum {max} sélection{max > 1 ? "s" : ""}
          {value.length > 0 && ` (${value.length}/${max})`}
        </div>
      )}
    </div>
  );
}

// Summary component showing active filters
interface FilterSummaryProps {
  schema: FilterSchema;
  values: Record<string, FilterValue>;
  onClear: (filterId: string) => void;
  onClearAll: () => void;
  className?: string;
}

export function FilterSummary({
  schema,
  values,
  onClear,
  onClearAll,
  className,
}: FilterSummaryProps) {
  const activeFilters = schema.filter((field) => {
    const value = values[field.id];
    if (Array.isArray(value)) return value.length > 0;
    if (typeof value === "object" && value !== null) {
      return Object.values(value).some(v => v !== null && v !== "");
    }
    return value !== "" && value !== null && value !== undefined;
  });

  if (activeFilters.length === 0) {
    return null;
  }

  return (
    <div className={cn("space-y-2", className)} data-testid="filter-summary">
      <div className="flex items-center justify-between">
        <span className="text-sm font-medium">Filtres actifs :</span>
        <Button
          variant="ghost"
          size="sm"
          onClick={onClearAll}
          className="h-6 px-2 text-xs"
          data-testid="clear-all-filters"
        >
          Tout effacer
        </Button>
      </div>
      
      <div className="flex flex-wrap gap-2">
        {activeFilters.map((field) => {
          const value = values[field.id];
          let displayValue = "";

          if (field.type === "select") {
            const option = field.options.find(opt => opt.value === value);
            displayValue = option?.label || String(value || "");
          } else if (Array.isArray(value)) {
            displayValue = `${value.length} sélectionné${value.length > 1 ? "s" : ""}`;
          } else {
            displayValue = String(value);
          }

          return (
            <Badge
              key={field.id}
              variant="secondary"
              className="cursor-pointer"
              onClick={() => onClear(field.id)}
              data-testid={`active-filter-${field.id}`}
            >
              {field.label}: {displayValue}
              <X className="ml-1 h-3 w-3" />
            </Badge>
          );
        })}
      </div>
    </div>
  );
}