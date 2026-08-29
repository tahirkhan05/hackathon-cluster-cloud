/**
 * React hooks for WebSocket integration.
 */
import { useEffect, useState, useCallback, useRef } from 'react';
import { getWebSocketClient, type RealtimeEvent, type EventHandler } from '@/lib/websocket';

/**
 * Hook for WebSocket connection status.
 */
export function useWebSocketConnection() {
  const [connected, setConnected] = useState(false);
  const [reconnecting, setReconnecting] = useState(false);
  const client = getWebSocketClient({
    onConnect: () => {
      setConnected(true);
      setReconnecting(false);
    },
    onDisconnect: () => {
      setConnected(false);
      setReconnecting(true);
    },
  });

  useEffect(() => {
    client.connect();

    const pingInterval = setInterval(() => {
      if (client.isConnected()) {
        client.ping();
      }
    }, 30000);

    return () => {
      clearInterval(pingInterval);
    };
  }, []);

  return { connected, reconnecting };
}

/**
 * Hook for subscribing to specific event types.
 */
export function useRealtimeEvent(
  eventType: string | string[],
  handler: EventHandler
) {
  const client = getWebSocketClient();
  const handlerRef = useRef(handler);

  useEffect(() => {
    handlerRef.current = handler;
  }, [handler]);

  useEffect(() => {
    const eventTypes = Array.isArray(eventType) ? eventType : [eventType];
    const unsubscribers: (() => void)[] = [];

    eventTypes.forEach((type) => {
      const unsub = client.on(type, (event) => handlerRef.current(event));
      unsubscribers.push(unsub);
    });

    return () => {
      unsubscribers.forEach((unsub) => unsub());
    };
  }, [eventType]);
}

/**
 * Hook for all realtime events (for activity feed).
 */
export function useAllRealtimeEvents(handler: EventHandler) {
  return useRealtimeEvent('*', handler);
}

/**
 * Hook for accumulating events into a feed.
 */
export function useEventFeed(maxEvents: number = 50) {
  const [events, setEvents] = useState<RealtimeEvent[]>([]);

  const handleEvent = useCallback((event: RealtimeEvent) => {
    setEvents((prev) => {
      const newEvents = [event, ...prev];
      return newEvents.slice(0, maxEvents);
    });
  }, [maxEvents]);

  useAllRealtimeEvents(handleEvent);

  const clearEvents = useCallback(() => {
    setEvents([]);
  }, []);

  return { events, clearEvents };
}

/**
 * Hook for tracking specific entity updates (e.g., a job).
 */
export function useEntityEvents(entityId: string, entityType: 'job' | 'node' | 'task') {
  const [events, setEvents] = useState<RealtimeEvent[]>([]);

  const handleEvent = useCallback((event: RealtimeEvent) => {
    const data = event.data;
    
    const isRelated = 
      (entityType === 'job' && data.job_id === entityId) ||
      (entityType === 'node' && data.node_id === entityId) ||
      (entityType === 'task' && data.task_id === entityId);

    if (isRelated) {
      setEvents((prev) => [event, ...prev].slice(0, 20));
    }
  }, [entityId, entityType]);

  useAllRealtimeEvents(handleEvent);

  return events;
}
