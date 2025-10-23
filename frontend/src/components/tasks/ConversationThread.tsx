"use client";

import React, { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { FileUploadField } from '@/components/forms/FileUploadField';
import {
  Send,
  Loader2,
  MessageSquare,
  Bot,
  User,
  AlertCircle
} from 'lucide-react';
import type { ConversationMessage, HumanInputRequest } from '@/lib/types/recipes';

interface ConversationThreadProps {
  messages: ConversationMessage[];
  humanInputRequest: HumanInputRequest;
  onSubmitResponse: (response: string | Record<string, any>, files?: File[]) => Promise<void>;
  loading?: boolean;
  error?: string;
}

export function ConversationThread({
  messages,
  humanInputRequest,
  onSubmitResponse,
  loading,
  error
}: ConversationThreadProps) {
  const [textResponse, setTextResponse] = useState('');
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    // Validate based on input type
    if (humanInputRequest.input_type === 'text' && !textResponse.trim()) {
      setValidationError('Veuillez saisir une réponse');
      return;
    }

    if (humanInputRequest.input_type === 'file' && uploadedFiles.length === 0) {
      setValidationError('Veuillez sélectionner au moins un fichier');
      return;
    }

    try {
      let response: string | Record<string, any>;

      switch (humanInputRequest.input_type) {
        case 'text':
          response = textResponse.trim();
          await onSubmitResponse(response);
          break;

        case 'file':
        case 'multiple_files':
          response = { message: textResponse.trim() || 'Fichiers fournis' };
          await onSubmitResponse(response, uploadedFiles);
          break;

        case 'choice':
          if (!textResponse) {
            setValidationError('Veuillez faire un choix');
            return;
          }
          response = textResponse;
          await onSubmitResponse(response);
          break;

        default:
          response = textResponse.trim();
          await onSubmitResponse(response);
      }

      // Reset form
      setTextResponse('');
      setUploadedFiles([]);
    } catch (error) {
      console.error('Error submitting response:', error);
    }
  };

  const renderMessage = (message: ConversationMessage) => {
    const isBot = message.type === 'assistant' || message.type === 'system';

    return (
      <div
        key={message.id}
        className={`flex gap-3 ${isBot ? 'justify-start' : 'justify-end'}`}
      >
        {isBot && (
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0">
            <Bot className="h-4 w-4 text-white" />
          </div>
        )}

        <div className={`max-w-lg ${isBot ? 'order-1' : 'order-0'}`}>
          <Card className={`p-4 ${
            isBot
              ? 'bg-slate-50 border-slate-200'
              : 'bg-blue-50 border-blue-200 ml-auto'
          }`}>
            <p className="text-sm text-slate-900 whitespace-pre-wrap">
              {message.content}
            </p>

            {message.files && message.files.length > 0 && (
              <div className="mt-3 space-y-1">
                {message.files.map((file, index) => (
                  <div key={index} className="flex items-center gap-2 text-xs text-slate-600">
                    <span>📎</span>
                    <span>{file.name}</span>
                  </div>
                ))}
              </div>
            )}

            <div className="text-xs text-slate-500 mt-2">
              {new Date(message.timestamp).toLocaleTimeString('fr-FR', {
                hour: '2-digit',
                minute: '2-digit'
              })}
            </div>
          </Card>
        </div>

        {!isBot && (
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-green-500 to-teal-600 flex items-center justify-center flex-shrink-0">
            <User className="h-4 w-4 text-white" />
          </div>
        )}
      </div>
    );
  };

  const renderInputField = () => {
    switch (humanInputRequest.input_type) {
      case 'file':
      case 'multiple_files':
        return (
          <div className="space-y-4">
            <FileUploadField
              name="response_files"
              label="Fichiers demandés"
              description="Sélectionnez les fichiers à fournir"
              multiple={humanInputRequest.input_type === 'multiple_files'}
              required={true}
              value={uploadedFiles}
              onChange={setUploadedFiles}
              error={validationError}
            />
            {humanInputRequest.input_type === 'multiple_files' && (
              <div className="space-y-2">
                <Label htmlFor="context_message">
                  Message optionnel
                </Label>
                <Textarea
                  id="context_message"
                  placeholder="Ajoutez un commentaire sur les fichiers fournis..."
                  value={textResponse}
                  onChange={(e) => setTextResponse(e.target.value)}
                  rows={2}
                />
              </div>
            )}
          </div>
        );

      case 'choice':
        return (
          <div className="space-y-3">
            <Label>Choisissez une option :</Label>
            <div className="space-y-2">
              {humanInputRequest.choices?.map((choice, index) => (
                <label key={index} className="flex items-center space-x-2 cursor-pointer">
                  <input
                    type="radio"
                    name="choice"
                    value={choice}
                    checked={textResponse === choice}
                    onChange={(e) => setTextResponse(e.target.value)}
                    className="text-blue-600"
                  />
                  <span className="text-sm">{choice}</span>
                </label>
              ))}
            </div>
            {validationError && (
              <div className="flex items-center gap-2 text-sm text-red-600">
                <AlertCircle className="h-4 w-4" />
                {validationError}
              </div>
            )}
          </div>
        );

      case 'text':
      default:
        return (
          <div className="space-y-2">
            <Label htmlFor="text_response">
              Votre réponse
            </Label>
            <Textarea
              id="text_response"
              placeholder="Tapez votre réponse..."
              value={textResponse}
              onChange={(e) => setTextResponse(e.target.value)}
              rows={3}
              className={validationError ? 'border-red-400' : ''}
            />
            {validationError && (
              <div className="flex items-center gap-2 text-sm text-red-600">
                <AlertCircle className="h-4 w-4" />
                {validationError}
              </div>
            )}
          </div>
        );
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <MessageSquare className="h-6 w-6 text-purple-600" />
        <h3 className="text-lg font-semibold text-slate-900">
          Conversation avec l'agent
        </h3>
      </div>

      {/* Messages history */}
      {messages.length > 0 && (
        <Card className="p-4 max-h-80 overflow-y-auto">
          <div className="space-y-4">
            {messages.map(renderMessage)}
          </div>
        </Card>
      )}

      {/* Current question */}
      <Card className="p-6 border-purple-200 bg-purple-50">
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-full bg-gradient-to-br from-purple-500 to-purple-600 flex items-center justify-center flex-shrink-0">
            <Bot className="h-4 w-4 text-white" />
          </div>
          <div className="flex-1">
            <h4 className="font-medium text-purple-900 mb-2">
              Question de l'agent :
            </h4>
            <p className="text-purple-800 whitespace-pre-wrap">
              {humanInputRequest.question}
            </p>
            {humanInputRequest.context && (
              <div className="mt-3 p-3 bg-white/60 rounded-lg">
                <p className="text-sm text-purple-700">
                  <strong>Contexte :</strong> {humanInputRequest.context}
                </p>
              </div>
            )}
          </div>
        </div>
      </Card>

      {/* Error display */}
      {error && (
        <Card className="p-4 border-red-200 bg-red-50">
          <div className="flex items-center gap-2 text-red-700">
            <AlertCircle className="h-5 w-5" />
            <p className="font-medium">Erreur lors de l'envoi</p>
          </div>
          <p className="text-sm text-red-600 mt-1">{error}</p>
        </Card>
      )}

      {/* Response form */}
      <Card className="p-6">
        <form onSubmit={handleSubmit} className="space-y-4">
          {renderInputField()}

          <Button
            type="submit"
            disabled={loading}
            className="w-full bg-gradient-to-r from-purple-600 to-purple-700 hover:from-purple-700 hover:to-purple-800"
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin mr-2" />
                Envoi en cours...
              </>
            ) : (
              <>
                <Send className="h-4 w-4 mr-2" />
                Envoyer la réponse
              </>
            )}
          </Button>
        </form>
      </Card>
    </div>
  );
}