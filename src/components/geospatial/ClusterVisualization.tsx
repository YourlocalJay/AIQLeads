import React, { useMemo, useState, useEffect } from 'react';
import { Card } from '@/components/ui/card';
import { Slider } from '@/components/ui/slider';
import { Label } from '@/components/ui/label';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { WebSocketClient } from '@/utils/websocket'; // Hypothetical WebSocket client

interface ClusterFeature {
  type: 'Feature';
  geometry: {
    type: 'MultiPoint';
    coordinates: [number, number][];
  };
  properties: {
    cluster_id: number;
    lead_count: number;
  };
}

interface ClusterData {
  type: 'FeatureCollection';
  features: ClusterFeature[];
}

interface ClusterVisualizationProps {
  data: ClusterData;
  width?: number;
  height?: number;
  clusterRadius?: number;
  minPoints?: number;
  onClusterParamsChange?: (radius: number, minPoints: number) => void;
  className?: string;
}

export const ClusterVisualization: React.FC<ClusterVisualizationProps> = ({
  data,
  width = 800,
  height = 600,
  clusterRadius = 5000,
  minPoints = 5,
  onClusterParamsChange,
  className = ''
}) => {
  const [hoveredCluster, setHoveredCluster] = useState<number | null>(null);

  // WebSocket connection for real-time updates
  useEffect(() => {
    const ws = new WebSocketClient('wss://realtime.aiqleads.com/clusters', (newData: ClusterData) => {
      data.features = newData.features;
    });

    return () => ws.disconnect();
  }, []);

  // Generate colors for clusters
  const clusterColors = useMemo(() => {
    const colors = ['#3B82F6', '#EF4444', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899', '#14B8A6', '#F97316', '#6366F1', '#06B6D4'];
    const clusterIds = new Set(data.features.map(f => f.properties.cluster_id));
    const colorMap = new Map<number, string>();

    Array.from(clusterIds).forEach((id, index) => {
      colorMap.set(id, colors[index % colors.length]);
    });

    return colorMap;
  }, [data]);

  // Calculate bounds and scaling
  const { bounds, scale } = useMemo(() => {
    const allPoints = data.features.flatMap(f => f.geometry.coordinates);
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

  // Transform points to SVG coordinates
  const transformedClusters = useMemo(() => {
    return data.features.map(feature => {
      const points = feature.geometry.coordinates.map(([x, y]) => ({
        x: 40 + (x - bounds.minX) * scale,
        y: height - (40 + (y - bounds.minY) * scale)
      }));

      const centroid = points.reduce((acc, point) => ({
        x: acc.x + point.x / points.length,
        y: acc.y + point.y / points.length
      }), { x: 0, y: 0 });

      return {
        id: feature.properties.cluster_id,
        points,
        centroid,
        leadCount: feature.properties.lead_count,
        color: clusterColors.get(feature.properties.cluster_id) || '#888888'
      };
    });
  }, [data, bounds, scale, height, clusterColors]);

  return (
    <Card className={`p-4 ${className}`}>
      <div className="flex gap-4 mb-4">
        <div className="flex-1">
          <Label>Cluster Radius (meters)</Label>
          <Slider
            value={[clusterRadius]}
            onValueChange={([value]) => onClusterParamsChange?.(value, minPoints)}
            min={1000}
            max={10000}
            step={500}
            className="w-full"
          />
          <div className="text-sm text-muted-foreground mt-1">
            {clusterRadius}m
          </div>
        </div>

        <div className="w-48">
          <Label>Minimum Points</Label>
          <Select value={String(minPoints)} onValueChange={(value) => onClusterParamsChange?.(clusterRadius, parseInt(value))}>
            <SelectTrigger><SelectValue placeholder="Min points" /></SelectTrigger>
            <SelectContent>
              {[3, 5, 10, 15, 20].map(n => (
                <SelectItem key={n} value={String(n)}>{n} points</SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>

      <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`} className="bg-background">
        {transformedClusters.map(cluster => (
          <Tooltip key={`cluster-${cluster.id}`}>
            <TooltipTrigger asChild>
              <g>
                <path
                  d={`M ${cluster.points.map(p => `${p.x},${p.y}`).join(' L ')} Z`}
                  fill={cluster.color} fillOpacity={0.1}
                  stroke={cluster.color} strokeWidth={1}
                  onMouseEnter={() => setHoveredCluster(cluster.id)}
                  onMouseLeave={() => setHoveredCluster(null)}
                />
                <circle cx={cluster.centroid.x} cy={cluster.centroid.y} r={6} fill={cluster.color} stroke="white" strokeWidth={2} />
              </g>
            </TooltipTrigger>
            <TooltipContent>
              <p><strong>Cluster {cluster.id}</strong></p>
              <p>Leads: {cluster.leadCount}</p>
            </TooltipContent>
          </Tooltip>
        ))}
      </svg>
    </Card>
  );
};
