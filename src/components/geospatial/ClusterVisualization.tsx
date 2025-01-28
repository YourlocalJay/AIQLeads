import React, { useMemo } from 'react';
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

interface ClusterFeature {
  type: 'Feature';
  geometry: {
    type: 'MultiPoint';
    coordinates: [number, number][];
  };
  properties: {
    cluster_id: number;
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
  // Generate colors for clusters
  const clusterColors = useMemo(() => {
    const colors = [
      '#3B82F6', // blue
      '#EF4444', // red
      '#10B981', // green
      '#F59E0B', // yellow
      '#8B5CF6', // purple
      '#EC4899', // pink
      '#14B8A6', // teal
      '#F97316', // orange
      '#6366F1', // indigo
      '#06B6D4'  // cyan
    ];
    
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
    
    return {
      bounds,
      scale: Math.min(xScale, yScale)
    };
  }, [data, width, height]);

  // Transform points to SVG coordinates
  const transformedClusters = useMemo(() => {
    return data.features.map(feature => {
      const points = feature.geometry.coordinates.map(([x, y]) => ({
        x: 40 + (x - bounds.minX) * scale,
        y: height - (40 + (y - bounds.minY) * scale)
      }));
      
      // Calculate cluster centroid
      const centroid = points.reduce(
        (acc, point) => ({
          x: acc.x + point.x / points.length,
          y: acc.y + point.y / points.length
        }),
        { x: 0, y: 0 }
      );
      
      return {
        id: feature.properties.cluster_id,
        points,
        centroid,
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
          <Select
            value={String(minPoints)}
            onValueChange={(value) => onClusterParamsChange?.(clusterRadius, parseInt(value))}
          >
            <SelectTrigger>
              <SelectValue placeholder="Min points" />
            </SelectTrigger>
            <SelectContent>
              {[3, 5, 10, 15, 20].map(n => (
                <SelectItem key={n} value={String(n)}>
                  {n} points
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      </div>
      
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        className="bg-background"
      >
        {/* Draw cluster convex hulls */}
        {transformedClusters.map(cluster => (
          <g key={`hull-${cluster.id}`}>
            <path
              d={`M ${cluster.points.map(p => `${p.x},${p.y}`).join(' L ')} Z`}
              fill={cluster.color}
              fillOpacity={0.1}
              stroke={cluster.color}
              strokeWidth={1}
            />
          </g>
        ))}
        
        {/* Draw points */}
        {transformedClusters.map(cluster => (
          <g key={`points-${cluster.id}`}>
            {cluster.points.map((point, i) => (
              <circle
                key={i}
                cx={point.x}
                cy={point.y}
                r={4}
                fill={cluster.color}
              />
            ))}
            
            {/* Draw cluster centroid and label */}
            <circle
              cx={cluster.centroid.x}
              cy={cluster.centroid.y}
              r={6}
              fill={cluster.color}
              stroke="white"
              strokeWidth={2}
            />
            <text
              x={cluster.centroid.x}
              y={cluster.centroid.y - 10}
              textAnchor="middle"
              fill="currentColor"
              fontSize={12}
              fontWeight="bold"
            >
              Cluster {cluster.id}
            </text>
          </g>
        ))}
        
        {/* Legend */}
        <g transform={`translate(${width - 150}, 20)`}>
          <rect width={130} height={30 * transformedClusters.length} fill="white" opacity={0.9} rx={4} />
          {transformedClusters.map((cluster, i) => (
            <g key={`legend-${cluster.id}`} transform={`translate(10, ${10 + i * 25})`}>
              <circle cx={8} cy={8} r={6} fill={cluster.color} />
              <text x={20} y={12} fontSize={12} fill="currentColor">
                Cluster {cluster.id} ({cluster.points.length} leads)
              </text>
            </g>
          ))}
        </g>
      </svg>
    </Card>
  );
};