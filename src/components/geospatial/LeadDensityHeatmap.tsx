import React, { useMemo, useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Slider } from '@/components/ui/slider';
import { Label } from '@/components/ui/label';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { ZoomPanSvg } from '@/components/ui/zoom-pan-svg'; // Hypothetical component for zoom/pan support
import { WebSocketClient } from '@/utils/websocket'; // Hypothetical WebSocket client for real-time updates

interface HeatmapFeature {
  type: 'Feature';
  geometry: {
    type: 'Point';
    coordinates: [number, number];
  };
  properties: {
    count: number;
    forecasted_count?: number;
  };
}

interface HeatmapData {
  type: 'FeatureCollection';
  features: HeatmapFeature[];
}

interface LeadDensityHeatmapProps {
  data: HeatmapData;
  width?: number;
  height?: number;
  gridSize?: number;
  onGridSizeChange?: (size: number) => void;
  className?: string;
}

export const LeadDensityHeatmap: React.FC<LeadDensityHeatmapProps> = ({
  data,
  width = 800,
  height = 600,
  gridSize = 1000,
  onGridSizeChange,
  className = ''
}) => {
  const [hoveredPoint, setHoveredPoint] = useState<HeatmapFeature | null>(null);
  const [forecastWindow, setForecastWindow] = useState<number>(30); // Forecast window in days

  // WebSocket client for real-time updates
  useEffect(() => {
    const ws = new WebSocketClient('wss://realtime.aiqleads.com/density-updates', (newData: HeatmapData) => {
      data.features = newData.features;
    });

    return () => ws.disconnect();
  }, []);

  // Calculate bounds for scaling
  const bounds = useMemo(() => {
    if (!data.features.length) return { minX: 0, maxX: 0, minY: 0, maxY: 0 };

    return data.features.reduce((acc, feature) => {
      const [x, y] = feature.geometry.coordinates;
      return {
        minX: Math.min(acc.minX, x),
        maxX: Math.max(acc.maxX, x),
        minY: Math.min(acc.minY, y),
        maxY: Math.max(acc.maxY, y)
      };
    }, {
      minX: Infinity,
      maxX: -Infinity,
      minY: Infinity,
      maxY: -Infinity
    });
  }, [data]);

  // Calculate scaling factors
  const scale = useMemo(() => {
    const { minX, maxX, minY, maxY } = bounds;
    const padding = 20;
    
    const xScale = (width - 2 * padding) / (maxX - minX);
    const yScale = (height - 2 * padding) / (maxY - minY);
    
    return Math.min(xScale, yScale);
  }, [bounds, width, height]);

  // Transform coordinates to SVG space
  const points = useMemo(() => {
    const { minX, minY } = bounds;
    const padding = 20;
    
    return data.features.map(feature => {
      const [x, y] = feature.geometry.coordinates;
      return {
        x: padding + (x - minX) * scale,
        y: height - (padding + (y - minY) * scale),
        count: feature.properties.count,
        forecastedCount: feature.properties.forecasted_count || feature.properties.count,
        feature
      };
    });
  }, [data, bounds, scale, height]);

  // Determine color intensity for heatmap
  const maxCount = useMemo(() => {
    return Math.max(...points.map(p => p.count), 1);
  }, [points]);

  const getColor = (count: number) => {
    const intensity = count / maxCount;
    return `rgba(255, 69, 0, ${intensity})`; // Red heatmap with varying opacity
  };

  return (
    <Card className={`p-4 ${className}`}>
      <div className="mb-4 flex justify-between">
        <div>
          <Label>Grid Size (meters)</Label>
          <Slider
            value={[gridSize]}
            onValueChange={([value]) => onGridSizeChange?.(value)}
            min={100}
            max={5000}
            step={100}
            className="w-40"
          />
          <div className="text-sm text-muted-foreground mt-1">
            {gridSize}m × {gridSize}m
          </div>
        </div>

        <div>
          <Label>Forecast Window (days)</Label>
          <Slider
            value={[forecastWindow]}
            onValueChange={([value]) => setForecastWindow(value)}
            min={7}
            max={90}
            step={7}
            className="w-40"
          />
          <div className="text-sm text-muted-foreground mt-1">
            {forecastWindow} days
          </div>
        </div>
      </div>

      <ZoomPanSvg width={width} height={height}>
        {/* Heatmap Circles */}
        {points.map((point, i) => (
          <Tooltip key={i}>
            <TooltipTrigger asChild>
              <circle
                cx={point.x}
                cy={point.y}
                r={gridSize * scale / 2000}
                fill={getColor(point.forecastedCount)}
                opacity={0.7}
                onMouseEnter={() => setHoveredPoint(point.feature)}
                onMouseLeave={() => setHoveredPoint(null)}
              />
            </TooltipTrigger>
            <TooltipContent>
              <p><strong>Leads:</strong> {point.count}</p>
              <p><strong>Forecast:</strong> {point.forecastedCount}</p>
            </TooltipContent>
          </Tooltip>
        ))}

        {/* Legend */}
        <g transform={`translate(${width - 120}, ${height - 120})`}>
          <rect width={100} height={100} fill="white" opacity={0.9} rx={4} />
          {[0.2, 0.4, 0.6, 0.8, 1].map((intensity, i) => (
            <g key={i} transform={`translate(10, ${10 + i * 20})`}>
              <rect width={15} height={15} fill={`rgba(255, 69, 0, ${intensity})`} />
              <text x={25} y={12} fontSize={12} fill="currentColor">
                {Math.round(maxCount * intensity)}
              </text>
            </g>
          ))}
        </g>
      </ZoomPanSvg>
    </Card>
  );
};
