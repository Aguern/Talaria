"use client";

import React, { useState, useEffect } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { sessionStorage, authAPI } from '@/lib/api';
import { apiClient } from '@/lib/api-client';

export default function DebugPage() {
  const [session, setSession] = useState<any>(null);
  const [userInfo, setUserInfo] = useState<any>(null);
  const [testResults, setTestResults] = useState<any>({});

  useEffect(() => {
    checkSession();
  }, []);

  const checkSession = () => {
    const sess = sessionStorage.get();
    setSession(sess);
    console.log('Session:', sess);
  };

  const testGetMe = async () => {
    try {
      const user = await authAPI.getMe();
      setUserInfo(user);
      setTestResults(prev => ({ ...prev, getMe: '✅ Success' }));
    } catch (error: any) {
      setTestResults(prev => ({ ...prev, getMe: `❌ ${error.message}` }));
    }
  };

  const testMCPRecipes = async () => {
    try {
      const recipes = await apiClient.get('/mcp/recipes');
      setTestResults(prev => ({ ...prev, recipes: '✅ Success' }));
      console.log('MCP Recipes success');
    } catch (error: any) {
      setTestResults(prev => ({ ...prev, recipes: `❌ ${error.message}` }));
      console.error('MCP Recipes error:', error);
    }
  };

  const testConversations = async () => {
    try {
      const convs = await apiClient.get('/conversations');
      setTestResults(prev => ({ ...prev, conversations: '✅ Success' }));
      console.log('Conversations success');
    } catch (error: any) {
      setTestResults(prev => ({ ...prev, conversations: `❌ ${error.message}` }));
      console.error('Conversations error:', error);
    }
  };

  const loginTest = async () => {
    try {
      await authAPI.login({ email: 'test@example.com', password: 'test123' });
      checkSession();
      setTestResults(prev => ({ ...prev, login: '✅ Success' }));
    } catch (error: any) {
      setTestResults(prev => ({ ...prev, login: `❌ ${error.message}` }));
    }
  };

  const decodeToken = (token: string) => {
    try {
      const parts = token.split('.');
      const payload = JSON.parse(atob(parts[1]));
      const exp = new Date(payload.exp * 1000);
      const now = new Date();
      return {
        ...payload,
        expiresAt: exp.toLocaleString(),
        isExpired: exp < now,
        timeLeft: Math.floor((exp.getTime() - now.getTime()) / 1000 / 60) + ' minutes'
      };
    } catch {
      return null;
    }
  };

  return (
    <div className="container mx-auto p-8 max-w-4xl">
      <h1 className="text-3xl font-bold mb-8">🔧 Debug Authentication</h1>

      <Card className="p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Session Storage</h2>
        {session ? (
          <div className="space-y-2">
            <p><strong>Token:</strong> {session.token ? `${session.token.substring(0, 30)}...` : 'NO TOKEN'}</p>
            <p><strong>Client ID:</strong> {session.clientId || 'None'}</p>
            {session.token && (
              <div className="mt-4 p-4 bg-muted rounded">
                <h3 className="font-semibold mb-2">Token Info:</h3>
                <pre className="text-sm">{JSON.stringify(decodeToken(session.token), null, 2)}</pre>
              </div>
            )}
          </div>
        ) : (
          <p className="text-muted-foreground">No session found</p>
        )}
      </Card>

      <Card className="p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">Test Actions</h2>
        <div className="space-x-2 mb-4">
          <Button onClick={loginTest} variant="outline">Login as test@example.com</Button>
          <Button onClick={checkSession} variant="outline">Refresh Session</Button>
          <Button onClick={() => { sessionStorage.clear(); checkSession(); }} variant="destructive">Clear Session</Button>
        </div>
      </Card>

      <Card className="p-6 mb-6">
        <h2 className="text-xl font-semibold mb-4">API Tests</h2>
        <div className="space-x-2 mb-4">
          <Button onClick={testGetMe} variant="outline">Test /users/me</Button>
          <Button onClick={testMCPRecipes} variant="outline">Test /mcp/recipes</Button>
          <Button onClick={testConversations} variant="outline">Test /conversations</Button>
        </div>

        {Object.keys(testResults).length > 0 && (
          <div className="mt-4 p-4 bg-muted rounded">
            <h3 className="font-semibold mb-2">Results:</h3>
            {Object.entries(testResults).map(([key, value]) => (
              <p key={key}><strong>{key}:</strong> {value}</p>
            ))}
          </div>
        )}
      </Card>

      {userInfo && (
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4">User Info</h2>
          <pre className="text-sm">{JSON.stringify(userInfo, null, 2)}</pre>
        </Card>
      )}
    </div>
  );
}