"use client";

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { FileUploadField } from './FileUploadField';
import { Loader2, Send, AlertCircle } from 'lucide-react';
import type { RecipeManifest, InputParameter } from '@/lib/types/recipes';

interface DynamicFormProps {
  recipe: RecipeManifest;
  onSubmit: (formData: FormData) => Promise<void>;
  loading?: boolean;
  error?: string;
}

interface FormState {
  [key: string]: any;
}

export function DynamicForm({ recipe, onSubmit, loading, error }: DynamicFormProps) {
  const [formState, setFormState] = useState<FormState>({});
  const [validationErrors, setValidationErrors] = useState<Record<string, string>>({});

  const updateField = (name: string, value: any) => {
    setFormState(prev => ({ ...prev, [name]: value }));
    // Clear validation error when user starts typing
    if (validationErrors[name]) {
      setValidationErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};

    recipe.inputs.forEach(input => {
      const value = formState[input.name];

      if (input.required) {
        if (input.type === 'file') {
          if (!value || (Array.isArray(value) && value.length === 0)) {
            errors[input.name] = 'Ce fichier est requis';
          }
        } else if (!value || (typeof value === 'string' && value.trim() === '')) {
          errors[input.name] = 'Ce champ est requis';
        }
      }
    });

    setValidationErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    // Prepare FormData
    const formData = new FormData();

    // Prepare request data
    const requestData = {
      context: formState.context || '',
      additional_data: {}
    };

    // Add non-file inputs to additional_data
    recipe.inputs.forEach(input => {
      if (input.type !== 'file' && formState[input.name] !== undefined) {
        if (input.name === 'context') {
          requestData.context = formState[input.name];
        } else {
          requestData.additional_data[input.name] = formState[input.name];
        }
      }
    });

    // Add request data as JSON
    formData.append('request', JSON.stringify(requestData));

    // Add files
    recipe.inputs.forEach(input => {
      if (input.type === 'file' && formState[input.name]) {
        const files = formState[input.name] as File[];
        files.forEach(file => {
          formData.append('files', file);
        });
      }
    });

    try {
      await onSubmit(formData);
    } catch (error) {
      console.error('Form submission error:', error);
    }
  };

  const renderField = (input: InputParameter) => {
    const value = formState[input.name];
    const hasError = !!validationErrors[input.name];
    const errorMessage = validationErrors[input.name];

    switch (input.type) {
      case 'file':
        return (
          <FileUploadField
            key={input.name}
            name={input.name}
            label={input.name === 'documents' ? 'Documents' : input.description}
            description={input.description}
            multiple={input.multiple}
            required={input.required}
            accept={input.name === 'documents' ? "application/pdf,application/msword,application/vnd.openxmlformats-officedocument.wordprocessingml.document,image/jpeg,image/png,text/plain" : "*/*"}
            value={value || []}
            onChange={(files) => updateField(input.name, files)}
            error={errorMessage}
          />
        );

      case 'text':
        if (input.name === 'context') {
          return (
            <div key={input.name} className="space-y-2">
              <Label htmlFor={input.name}>
                {input.description}
                {input.required && <span className="text-red-500 ml-1">*</span>}
              </Label>
              <Textarea
                id={input.name}
                placeholder="Ajoutez du contexte pour améliorer le traitement..."
                value={value || ''}
                onChange={(e) => updateField(input.name, e.target.value)}
                className={hasError ? 'border-red-400' : ''}
                rows={3}
              />
              {errorMessage && (
                <div className="flex items-center gap-2 text-sm text-red-600">
                  <AlertCircle className="h-4 w-4" />
                  {errorMessage}
                </div>
              )}
            </div>
          );
        } else {
          return (
            <div key={input.name} className="space-y-2">
              <Label htmlFor={input.name}>
                {input.description}
                {input.required && <span className="text-red-500 ml-1">*</span>}
              </Label>
              <Input
                id={input.name}
                type="text"
                value={value || ''}
                onChange={(e) => updateField(input.name, e.target.value)}
                className={hasError ? 'border-red-400' : ''}
                placeholder={`Entrez ${input.description.toLowerCase()}`}
              />
              {errorMessage && (
                <div className="flex items-center gap-2 text-sm text-red-600">
                  <AlertCircle className="h-4 w-4" />
                  {errorMessage}
                </div>
              )}
            </div>
          );
        }

      case 'number':
        return (
          <div key={input.name} className="space-y-2">
            <Label htmlFor={input.name}>
              {input.description}
              {input.required && <span className="text-red-500 ml-1">*</span>}
            </Label>
            <Input
              id={input.name}
              type="number"
              value={value || ''}
              onChange={(e) => updateField(input.name, parseFloat(e.target.value) || '')}
              className={hasError ? 'border-red-400' : ''}
              placeholder={`Entrez ${input.description.toLowerCase()}`}
            />
            {errorMessage && (
              <div className="flex items-center gap-2 text-sm text-red-600">
                <AlertCircle className="h-4 w-4" />
                {errorMessage}
              </div>
            )}
          </div>
        );

      case 'boolean':
        return (
          <div key={input.name} className="flex items-center space-x-2">
            <input
              id={input.name}
              type="checkbox"
              checked={value || false}
              onChange={(e) => updateField(input.name, e.target.checked)}
              className="h-4 w-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
            />
            <Label htmlFor={input.name} className="cursor-pointer">
              {input.description}
              {input.required && <span className="text-red-500 ml-1">*</span>}
            </Label>
            {errorMessage && (
              <div className="flex items-center gap-2 text-sm text-red-600">
                <AlertCircle className="h-4 w-4" />
                {errorMessage}
              </div>
            )}
          </div>
        );

      default:
        return (
          <div key={input.name} className="space-y-2">
            <Label htmlFor={input.name}>
              {input.description} ({input.type})
              {input.required && <span className="text-red-500 ml-1">*</span>}
            </Label>
            <Input
              id={input.name}
              type="text"
              value={value || ''}
              onChange={(e) => updateField(input.name, e.target.value)}
              className={hasError ? 'border-red-400' : ''}
              placeholder={`Entrez ${input.description.toLowerCase()}`}
            />
            {errorMessage && (
              <div className="flex items-center gap-2 text-sm text-red-600">
                <AlertCircle className="h-4 w-4" />
                {errorMessage}
              </div>
            )}
          </div>
        );
    }
  };

  return (
    <Card className="p-6">
      <form onSubmit={handleSubmit} className="space-y-6">
        {/* Form title */}
        <div className="text-center border-b pb-4">
          <h2 className="text-2xl font-semibold text-slate-900">
            {recipe.name}
          </h2>
          <p className="text-slate-600 mt-2">{recipe.description}</p>
        </div>

        {/* Error display */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4">
            <div className="flex items-center gap-2 text-red-700">
              <AlertCircle className="h-5 w-5" />
              <div>
                <h3 className="font-medium">Erreur de soumission</h3>
                <p className="text-sm text-red-600 mt-1">{error}</p>
              </div>
            </div>
          </div>
        )}

        {/* Form fields */}
        <div className="space-y-6">
          {recipe.inputs.map(renderField)}
        </div>

        {/* Submit button */}
        <div className="pt-4 border-t">
          <Button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-[#3898FF] to-[#8A78F2] hover:from-[#2980FF] hover:to-[#7B69F1] text-white"
            size="lg"
          >
            {loading ? (
              <>
                <Loader2 className="h-5 w-5 animate-spin mr-2" />
                Lancement en cours...
              </>
            ) : (
              <>
                <Send className="h-5 w-5 mr-2" />
                Lancer la recette
              </>
            )}
          </Button>
        </div>

        {/* Help text */}
        <div className="text-center">
          <p className="text-sm text-slate-500">
            Une fois lancée, vous serez redirigé vers la page de suivi de l'exécution
          </p>
        </div>
      </form>
    </Card>
  );
}