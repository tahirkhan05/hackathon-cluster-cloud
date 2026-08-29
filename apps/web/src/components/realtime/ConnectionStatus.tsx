'use client';

import { useWebSocketConnection } from '@/hooks/useWebSocket';
import { Wifi, WifiOff, RefreshCw } from 'lucide-react';

export function ConnectionStatus() {
  const { connected, reconnecting } = useWebSocketConnection();

  if (connected) {
    return (
      <div className="flex items-center gap-2 text-sm">
        <div className="relative">
          <Wifi className="w-4 h-4 text-green-600" />
          <div className="absolute -top-1 -right-1 w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
        </div>
        <span className="text-gray-600">Live</span>
      </div>
    );
  }

  if (reconnecting) {
    return (
      <div className="flex items-center gap-2 text-sm">
        <RefreshCw className="w-4 h-4 text-orange-600 animate-spin" />
        <span className="text-gray-600">Reconnecting...</span>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-2 text-sm">
      <WifiOff className="w-4 h-4 text-gray-400" />
      <span className="text-gray-500">Offline</span>
    </div>
  );
}
