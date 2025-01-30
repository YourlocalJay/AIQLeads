import React, { useEffect, useRef, useState } from 'react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Bell, CheckCircle2, XCircle } from 'lucide-react';

interface LeadUpdate {
  lead_id: number;
  status: string;
  update_type: string;
  timestamp: string;
  details: {
    score: number;
    source: string;
    priority: number;
  };
}

interface LeadNotificationsProps {
  apiKey: string;
  clientId: string;
  onUpdate?: (update: LeadUpdate) => void;
}

const LeadNotifications: React.FC<LeadNotificationsProps> = ({
  apiKey,
  clientId,
  onUpdate
}) => {
  const [notifications, setNotifications] = useState<LeadUpdate[]>([]);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  const connect = () => {
    try {
      const ws = new WebSocket(
        `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/leads/${clientId}`
      );

      ws.onopen = () => {
        ws.send(JSON.stringify({ type: 'auth', api_key: apiKey }));
        setConnected(true);
        if (reconnectTimeoutRef.current) {
          clearTimeout(reconnectTimeoutRef.current);
        }
      };

      ws.onmessage = (event) => {
        const update: LeadUpdate = JSON.parse(event.data);
        setNotifications(prev => [update, ...prev].slice(0, 50));
        if (onUpdate) {
          onUpdate(update);
        }
      };

      ws.onclose = () => {
        setConnected(false);
        // Attempt to reconnect after 5 seconds
        reconnectTimeoutRef.current = setTimeout(connect, 5000);
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        ws.close();
      };

      wsRef.current = ws;
    } catch (error) {
      console.error('Failed to connect to WebSocket:', error);
      setConnected(false);
    }
  };

  useEffect(() => {
    connect();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [apiKey, clientId]);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-2 mb-4">
        <Bell className="h-5 w-5" />
        <span className="font-medium">Lead Notifications</span>
        {connected ? (
          <CheckCircle2 className="h-4 w-4 text-green-500" />
        ) : (
          <XCircle className="h-4 w-4 text-red-500" />
        )}
      </div>

      <div className="space-y-2">
        {notifications.map((notification, index) => (
          <Alert key={`${notification.lead_id}-${notification.timestamp}-${index}`}>
            <AlertTitle>
              New {notification.update_type} - Lead #{notification.lead_id}
            </AlertTitle>
            <AlertDescription>
              <div className="text-sm">
                <p>Source: {notification.details.source}</p>
                <p>Score: {notification.details.score.toFixed(2)}</p>
                <p>Priority: {notification.details.priority.toFixed(2)}</p>
                <p className="text-xs text-gray-500 mt-1">
                  {new Date(notification.timestamp).toLocaleString()}
                </p>
              </div>
            </AlertDescription>
          </Alert>
        ))}
      </div>
    </div>
  );
};

export default LeadNotifications;