/**
 * WebSocket client with automatic reconnection.
 * 
 * Handles connection lifecycle, reconnection, and typed events.
 */

export interface RealtimeEvent {
  event_type: string;
  timestamp: string;
  data: Record<string, any>;
  metadata?: Record<string, any>;
}

export type EventHandler = (event: RealtimeEvent) => void;

interface WebSocketClientOptions {
  url?: string;
  reconnectInterval?: number;
  maxReconnectAttempts?: number;
  onConnect?: () => void;
  onDisconnect?: () => void;
  onError?: (error: Event) => void;
}

export class WebSocketClient {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectInterval: number;
  private maxReconnectAttempts: number;
  private reconnectAttempts: number = 0;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private eventHandlers: Map<string, EventHandler[]> = new Map();
  private isManualClose: boolean = false;
  
  // Lifecycle callbacks
  private onConnectCallback?: () => void;
  private onDisconnectCallback?: () => void;
  private onErrorCallback?: (error: Event) => void;

  constructor(options: WebSocketClientOptions = {}) {
    const apiUrl = options.url || process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const wsUrl = apiUrl.replace('http', 'ws');
    this.url = `${wsUrl}/ws/events`;
    
    this.reconnectInterval = options.reconnectInterval || 3000;
    this.maxReconnectAttempts = options.maxReconnectAttempts || 10;
    this.onConnectCallback = options.onConnect;
    this.onDisconnectCallback = options.onDisconnect;
    this.onErrorCallback = options.onError;
  }

  /**
   * Connect to WebSocket server.
   */
  connect(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log('[WebSocket] Already connected');
      return;
    }

    try {
      console.log('[WebSocket] Connecting to', this.url);
      this.ws = new WebSocket(this.url);

      this.ws.onopen = () => {
        console.log('[WebSocket] Connected');
        this.reconnectAttempts = 0;
        this.isManualClose = false;
        
        if (this.onConnectCallback) {
          this.onConnectCallback();
        }
      };

      this.ws.onmessage = (event) => {
        try {
          const data: RealtimeEvent = JSON.parse(event.data);
          this.handleEvent(data);
        } catch (error) {
          console.error('[WebSocket] Failed to parse message:', error);
        }
      };

      this.ws.onerror = (error) => {
        console.error('[WebSocket] Error:', error);
        if (this.onErrorCallback) {
          this.onErrorCallback(error);
        }
      };

      this.ws.onclose = () => {
        console.log('[WebSocket] Disconnected');
        this.ws = null;
        
        if (this.onDisconnectCallback) {
          this.onDisconnectCallback();
        }

        // Attempt reconnection if not manually closed
        if (!this.isManualClose) {
          this.scheduleReconnect();
        }
      };
    } catch (error) {
      console.error('[WebSocket] Connection failed:', error);
      this.scheduleReconnect();
    }
  }

  /**
   * Manually disconnect from WebSocket.
   */
  disconnect(): void {
    this.isManualClose = true;
    
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    console.log('[WebSocket] Manually disconnected');
  }

  /**
   * Subscribe to specific event type.
   */
  on(eventType: string, handler: EventHandler): () => void {
    if (!this.eventHandlers.has(eventType)) {
      this.eventHandlers.set(eventType, []);
    }
    
    this.eventHandlers.get(eventType)!.push(handler);

    // Return unsubscribe function
    return () => {
      const handlers = this.eventHandlers.get(eventType);
      if (handlers) {
        const index = handlers.indexOf(handler);
        if (index > -1) {
          handlers.splice(index, 1);
        }
      }
    };
  }

  /**
   * Subscribe to all events.
   */
  onAny(handler: EventHandler): () => void {
    return this.on('*', handler);
  }

  /**
   * Send ping to keep connection alive.
   */
  ping(): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send('ping');
    }
  }

  /**
   * Check if connected.
   */
  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Get reconnection status.
   */
  getStatus(): {
    connected: boolean;
    reconnectAttempts: number;
    maxAttempts: number;
  } {
    return {
      connected: this.isConnected(),
      reconnectAttempts: this.reconnectAttempts,
      maxAttempts: this.maxReconnectAttempts,
    };
  }

  // Private methods

  private handleEvent(event: RealtimeEvent): void {
    // Call wildcard handlers
    const wildcardHandlers = this.eventHandlers.get('*') || [];
    wildcardHandlers.forEach((handler) => handler(event));

    // Call specific event handlers
    const specificHandlers = this.eventHandlers.get(event.event_type) || [];
    specificHandlers.forEach((handler) => handler(event));
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.error(
        `[WebSocket] Max reconnection attempts (${this.maxReconnectAttempts}) reached`
      );
      return;
    }

    this.reconnectAttempts++;
    const delay = this.reconnectInterval * Math.min(this.reconnectAttempts, 5);

    console.log(
      `[WebSocket] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts}/${this.maxReconnectAttempts})`
    );

    this.reconnectTimeout = setTimeout(() => {
      this.connect();
    }, delay);
  }
}

// Singleton instance
let wsClient: WebSocketClient | null = null;

/**
 * Get or create WebSocket client singleton.
 */
export function getWebSocketClient(options?: WebSocketClientOptions): WebSocketClient {
  if (!wsClient) {
    wsClient = new WebSocketClient(options);
  }
  return wsClient;
}

/**
 * React hook for WebSocket events.
 */
export function useRealtimeEvents(
  eventType: string | string[],
  handler: EventHandler
): void {
  const client = getWebSocketClient();
  
  if (typeof window === 'undefined') {
    return; // Don't run on server
  }

  // Subscribe to events
  const eventTypes = Array.isArray(eventType) ? eventType : [eventType];
  const unsubscribers: (() => void)[] = [];

  eventTypes.forEach((type) => {
    const unsub = client.on(type, handler);
    unsubscribers.push(unsub);
  });

  // Cleanup on unmount
  return () => {
    unsubscribers.forEach((unsub) => unsub());
  };
}
