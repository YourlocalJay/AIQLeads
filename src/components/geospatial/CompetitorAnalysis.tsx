import React, { useMemo, useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Slider } from '@/components/ui/slider';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { WebSocketClient } from '@/utils/websocket'; // Hypothetical WebSocket client

interface CompetitorFeature {
  type: 'Feature';
  geometry: {
    type: 'Point';
    coordinates: [number, number];
  };
  properties: {
    lead_id: number;
    competitor_count: number;
    nearest_distance: number | null;
    competitors: Array<{
      location: [number, number];
      distance: number;
    }>;
  };
}

interface CompetitorData {
  type: 'FeatureCollection';
  features: CompetitorFeature[];
}

interface CompetitorAnalysisProps {
  data: CompetitorData;
  width?: number;
  height?: number;
  radius?: number;
  onRadiusChange?: (radius: number) => void;
  className?: string;
}

export const CompetitorAnalysis: React.FC<CompetitorAnalysisProps> = ({
  data,
  width = 800,
  height = 600,
  radius = 5000,
  onRadiusChange,
  className = ''
}) => {
  const [selectedLead, setSelectedLead] = useState<CompetitorFeature | null>(null);

  // WebSocket connection for real-time updates
  useEffect(() => {
    const ws = new WebSocketClient('wss://realtime.aiqleads.com/competitor-analysis', (newData: CompetitorData) => {
      data.features = newData.features;
    });

    return () => ws.disconnect();
  }, []);

  // Calculate bounds and scaling
  const { bounds, scale } = useMemo(() => {
    const allPoints = data.features.flatMap(f => [
      f.geometry.coordinates,
      ...f.properties.competitors.map(c => c.location)
    ]);
    
    if (!allPoints.length) return { bounds: { minX: 0, maxX: 0, minY: 0, maxY: 0 }, scale: 1 };
    
    const bounds = allPoints.reduce((acc, [x, y]) => ({
      minX: Math.min(acc.minX, x),
      maxX: Math.max(acc.maxX, x),
      minY: Math.min(acc.minY, y),
      maxY: Math.max(acc.maxY, y)
    }), {
      minX: Infinity,
      maxX: -Infinity,
      minY: Infinity,
      maxY: -Infinity
    });
    
    const padding = 40;
    const xScale = (width - 2 * padding) / (bounds.maxX - bounds.minX);
    const yScale = (height - 2 * padding) / (bounds.maxY - bounds.minY);
    
    return { bounds, scale: Math.min(xScale, yScale) };
  }, [data, width, height]);

  // Transform coordinates to SVG space
  const transformedData = useMemo(() => {
    return data.features.map(feature => {
      const [x, y] = feature.geometry.coordinates;
      const leadPoint = {
        x: 40 + (x - bounds.minX) * scale,
        y: height - (40 + (y - bounds.minY) * scale)
      };
      
      const competitors = feature.properties.competitors.map(comp => {
        const [compX, compY] = comp.location;
        return {
          x: 40 + (compX - bounds.minX) * scale,
          y: height - (40 + (compY - bounds.minY) * scale),
          distance: comp.distance
        };
      });
      
      return { ...feature, point: leadPoint, competitors };
    });
  }, [data, bounds, scale, height]);

  // Calculate statistics
  const stats = useMemo(() => {
    const distances = data.features.map(f => f.properties.nearest_distance).filter((d): d is number => d !== null);
    
    return {
      avgDistance: distances.reduce((a, b) => a + b, 0) / distances.length,
      maxDistance: Math.max(...distances),
      minDistance: Math.min(...distances),
      totalLeads: data.features.length,
      withCompetitors: data.features.filter(f => f.properties.competitor_count > 0).length,
      avgCompetitors: data.features.reduce((sum, f) => sum + f.properties.competitor_count, 0) / data.features.length,
      competitorRanges: {
        high: data.features.filter(f => f.properties.competitor_count > 5).length,
        medium: data.features.filter(f => f.properties.competitor_count > 2 && f.properties.competitor_count <= 5).length,
        low: data.features.filter(f => f.properties.competitor_count <= 2).length
      }
    };
  }, [data]);

  return (
    <Card className={`p-4 ${className}`}>
      <div className="flex justify-between items-start mb-4">
        <div className="w-64">
          <Label>Search Radius (meters)</Label>
          <Slider
            value={[radius]}
            onValueChange={([value]) => onRadiusChange?.(value)}
            min={1000}
            max={10000}
            step={500}
            className="w-full"
          />
          <div className="text-sm text-muted-foreground mt-1">
            {radius.toLocaleString()}m
          </div>
        </div>
      </div>

      <div className="flex gap-4">
        <div className="w-3/4">
          <svg width={width} height={height} className="bg-background">
            {/* Draw competition radius circles */}
            {transformedData.map((feature, i) => (
              <g key={`lead-${i}`}>
                <circle cx={feature.point.x} cy={feature.point.y} r={radius * scale / 1000}
                  fill="none" stroke="blue" strokeWidth={1} strokeDasharray="4 4" opacity={0.3} />

                {feature.competitors.map((comp, j) => (
                  <line key={`connection-${j}`} x1={feature.point.x} y1={feature.point.y}
                    x2={comp.x} y2={comp.y} stroke="red" strokeWidth={1} opacity={0.5} />
                ))}
              </g>
            ))}
          </svg>
        </div>

        <div className="w-1/4">
          {selectedLead ? (
            <div className="p-4 bg-background rounded-md">
              <h3 className="font-medium mb-2">Lead Details</h3>
              <p>Competitors: {selectedLead.properties.competitor_count}</p>
              <p>Nearest Competitor: {selectedLead.properties.nearest_distance?.toFixed(0)}m</p>
            </div>
          ) : (
            <p className="text-sm text-muted-foreground text-center mt-8">Select a lead to view details</p>
          )}
        </div>
      </div>
    </Card>
  );
};
