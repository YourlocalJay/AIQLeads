import React, { useMemo } from 'react';
import { Card } from '@/components/ui/card';
import { Slider } from '@/components/ui/slider';
import { Label } from '@/components/ui/label';

interface HeatmapFeature {
  type: 'Feature';
  geometry: {
    type: 'Point';
    coordinates: [number, number];
  };
  properties: {
    count: number;
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
  // Calculate bounds
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
        count: feature.properties.count
      };
    });
  }, [data, bounds, scale, height]);

  // Calculate color intensity
  const maxCount = useMemo(() => {
    return Math.max(...points.map(p => p.count));
  }, [points]);

  const getColor = (count: number) => {
    const intensity = count / maxCount;
    return `rgba(59, 130, 246, ${intensity})`; // Using blue with varying opacity
  };

  return (
    <Card className={`p-4 ${className}`}>
      <div className="mb-4">
        <Label>Grid Size (meters)</Label>
        <Slider
          value={[gridSize]}
          onValueChange={([value]) => onGridSizeChange?.(value)}
          min={100}
          max={5000}
          step={100}
          className="w-full"
        />
        <div className="text-sm text-muted-foreground mt-1">
          {gridSize}m × {gridSize}m
        </div>
      </div>
      
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        className="bg-background"
      >
        {/* Draw heatmap points */}
        {points.map((point, i) => (
          <circle
            key={i}
            cx={point.x}
            cy={point.y}
            r={gridSize * scale / 2000}
            fill={getColor(point.count)}
            opacity={0.6}
          >
            <title>Count: {point.count}</title>
          </circle>
        ))}
        
        {/* Draw grid (optional) */}
        {points.map((point, i) => (
          <rect
            key={`grid-${i}`}
            x={point.x - gridSize * scale / 2000}
            y={point.y - gridSize * scale / 2000}
            width={gridSize * scale / 1000}
            height={gridSize * scale / 1000}
            fill="none"
            stroke="rgba(156, 163, 175, 0.1)"
            strokeWidth={1}
          />
        ))}
        
        {/* Legend */}
        <g transform={`translate(${width - 100}, ${height - 120})`}>
          <rect x={0} y={0} width={80} height={100} fill="white" opacity={0.9} rx={4} />
          {[0.2, 0.4, 0.6, 0.8, 1].map((intensity, i) => (
            <g key={i} transform={`translate(10, ${10 + i * 20})`}>
              <rect
                width={15}
                height={15}
                fill={`rgba(59, 130, 246, ${intensity})`}
              />
              <text x={25} y={12} fontSize={12} fill="currentColor">
                {Math.round(maxCount * intensity)}
              </text>
            </g>
          ))}
        </g>
      </svg>
    </Card>
  );
};