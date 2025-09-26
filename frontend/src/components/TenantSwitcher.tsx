"use client";

import React from "react";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { Building2 } from "lucide-react";
import type { Tenant } from "@/lib/types";

interface TenantSwitcherProps {
  tenants: Tenant[];
  currentTenant?: string;
  onTenantChange: (tenantId: string) => void;
  className?: string;
}

export function TenantSwitcher({
  tenants,
  currentTenant,
  onTenantChange,
  className,
}: TenantSwitcherProps) {
  // Don't show switcher if only one tenant
  if (tenants.length <= 1) {
    const tenant = tenants[0];
    if (!tenant) return null;
    
    return (
      <Badge variant="outline" className={className} data-testid="single-tenant-badge">
        <Building2 className="mr-1 h-3 w-3" />
        Espace : {tenant.name || tenant.id}
      </Badge>
    );
  }

  const currentTenantData = tenants.find(t => t.id === currentTenant);

  return (
    <div className={className} data-testid="tenant-switcher">
      <Select value={currentTenant} onValueChange={onTenantChange}>
        <SelectTrigger className="w-[200px]" data-testid="tenant-selector">
          <div className="flex items-center">
            <Building2 className="mr-2 h-4 w-4" />
            <SelectValue placeholder="Sélectionner un espace" />
          </div>
        </SelectTrigger>
        <SelectContent>
          {tenants.map((tenant) => (
            <SelectItem key={tenant.id} value={tenant.id} data-testid={`tenant-option-${tenant.id}`}>
              <div className="flex items-center">
                <Building2 className="mr-2 h-4 w-4" />
                <div>
                  <div className="font-medium">
                    {tenant.name || tenant.id}
                  </div>
                  {tenant.name && tenant.name !== tenant.id && (
                    <div className="text-xs text-muted-foreground">
                      ID: {tenant.id}
                    </div>
                  )}
                </div>
              </div>
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </div>
  );
}