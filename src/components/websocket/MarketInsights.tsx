import React, { useEffect, useRef, useState } from 'react';
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { TrendingUp, TrendingDown, AlertTriangle, Activity } from 'lucide-react';

interface MarketEvent {
  event_type: string;
  timestamp: string;
  region: string;
  confidence: number;
  details: Record<string, any>;
  predicted_impact: number;
}

interface CompetitorActivity {
  competitor_id: string;
  activity_type: string;
  region: string;
  timestamp: string;
  details: Record<string, any>;
  threat_level: number;
}

interface AnalyticsData {
  current: {
    connections: number;
    messages_per_second: number;
    average_latency: number;
  };
  historical: {
    event_distribution: Record<string, number>;
    regional_activity: Record<string, number>;
    performance_metrics: Array<{
      timestamp: string;
      latency: number;
      message_count: number;
    }>;
  };
  predictions: {
    expected_events: number;
    predicted_hotspots: string[];
    confidence_scores: Record<string, number>;
  };
}

interface MarketInsightsProps {
  apiKey: string;
  clientId: string;
  regions?: string[];
  confidenceThreshold?: number;
}

const MarketInsights: React.FC<MarketInsightsProps> = ({
  apiKey,
  clientId,
  regions,
  confidenceThreshold = 0.7,
}) => {
  const [marketEvents, setMarketEvents] = useState<MarketEvent[]>([]);
  const [competitorActivities, setCompetitorActivities] = useState<CompetitorActivity[]>([]);
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [connected, setConnected] = useState(false);
  
  const marketWsRef = useRef<WebSocket | null>(null);
  const analyticsWsRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout>();

  const connectWebSockets = () => {
    // Connect to market events WebSocket
    const marketWs = new WebSocket(
      `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/market-events/${clientId}?${
        new URLSearchParams({
          ...(regions && { regions: regions.join(',') }),
          confidence_threshold: confidenceThreshold.toString(),
        })
      }`
    );

    marketWs.onopen = () => {
      marketWs.send(JSON.stringify({ type: 'auth', api_key: apiKey }));
      setConnected(true);
    };

    marketWs.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'market_events') {
        setMarketEvents(prev => [...data.events, ...prev].slice(0, 50));
      } else if (data.type === 'competitor_activity') {
        setCompetitorActivities(prev => [...data.activities, ...prev].slice(0, 50));
      }
    };

    // Connect to analytics WebSocket
    const analyticsWs = new WebSocket(
      `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/ws/analytics/${clientId}`
    );

    analyticsWs.onopen = () => {
      analyticsWs.send(JSON.stringify({ type: 'auth', api_key: apiKey }));
    };

    analyticsWs.onmessage = (event) => {
      const data = JSON.parse(event.data);
      if (data.type === 'analytics_update') {
        setAnalytics(data.metrics);
      }
    };

    // Handle connection errors and cleanup
    const handleClose = () => {
      setConnected(false);
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      reconnectTimeoutRef.current = setTimeout(connectWebSockets, 5000);
    };

    marketWs.onclose = handleClose;
    analyticsWs.onclose = handleClose;

    marketWsRef.current = marketWs;
    analyticsWsRef.current = analyticsWs;
  };

  useEffect(() => {
    connectWebSockets();
    return () => {
      if (marketWsRef.current) {
        marketWsRef.current.close();
      }
      if (analyticsWsRef.current) {
        analyticsWsRef.current.close();
      }
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
    };
  }, [apiKey, clientId, regions?.join(','), confidenceThreshold]);

  const renderMarketEvent = (event: MarketEvent) => (
    <Alert key={`${event.event_type}-${event.timestamp}`} className="mb-2">
      <AlertTriangle className="h-4 w-4" />
      <AlertTitle className="flex items-center gap-2">
        {event.event_type}
        {event.predicted_impact > 0 ? (
          <TrendingUp className="h-4 w-4 text-green-500" />
        ) : (
          <TrendingDown className="h-4 w-4 text-red-500" />
        )}
      </AlertTitle>
      <AlertDescription>
        <div className="text-sm">
          <p>Region: {event.region}</p>
          <p>Confidence: {(event.confidence * 100).toFixed(1)}%</p>
          <p>Impact: {(event.predicted_impact * 100).toFixed(1)}%</p>
          <p className="text-xs text-gray-500 mt-1">
            {new Date(event.timestamp).toLocaleString()}
          </p>
        </div>
      </AlertDescription>
    </Alert>
  );

  const renderCompetitorActivity = (activity: CompetitorActivity) => (
    <Alert 
      key={`${activity.competitor_id}-${activity.timestamp}`}
      className={`mb-2 ${activity.threat_level > 0.8 ? 'border-red-500' : ''}`}
    >
      <Activity className="h-4 w-4" />
      <AlertTitle>Competitor Activity - {activity.activity_type}</AlertTitle>
      <AlertDescription>
        <div className="text-sm">
          <p>Competitor: {activity.competitor_id}</p>
          <p>Region: {activity.region}</p>
          <p>Threat Level: {(activity.threat_level * 100).toFixed(1)}%</p>
          <p className="text-xs text-gray-500 mt-1">
            {new Date(activity.timestamp).toLocaleString()}
          </p>
        </div>
      </AlertDescription>
    </Alert>
  );

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card>
          <CardHeader>
            <CardTitle>Market Events</CardTitle>
          </CardHeader>
          <CardContent className="max-h-96 overflow-y-auto">
            {marketEvents.map(renderMarketEvent)}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Competitor Activities</CardTitle>
          </CardHeader>
          <CardContent className="max-h-96 overflow-y-auto">
            {competitorActivities.map(renderCompetitorActivity)}
          </CardContent>
        </Card>
      </div>

      {analytics && (
        <Card>
          <CardHeader>
            <CardTitle>Performance Analytics</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={analytics.historical.performance_metrics}>
                  <XAxis dataKey="timestamp" />
                  <YAxis />
                  <Tooltip />
                  <Line 
                    type="monotone" 
                    dataKey="latency" 
                    stroke="#8884d8" 
                    name="Latency (ms)" 
                  />
                  <Line 
                    type="monotone" 
                    dataKey="message_count" 
                    stroke="#82ca9d" 
                    name="Messages" 
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default MarketInsights;