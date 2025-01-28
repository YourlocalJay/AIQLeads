import React, { useMemo, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Slider } from '@/components/ui/slider';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';

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
    
    return {
      bounds,
      scale: Math.min(xScale, yScale)
    };
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
      
      return {
        ...feature,
        point: leadPoint,
        competitors
      };
    });
  }, [data, bounds, scale, height]);

  // Calculate statistics
  const stats = useMemo(() => {
    const distances = data.features
      .map(f => f.properties.nearest_distance)
      .filter((d): d is number => d !== null);
    
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

  // Color scales for competition intensity
  const getCompetitionColor = (count: number) => {
    if (count > 5) return '#EF4444'; // High - Red
    if (count > 2) return '#F59E0B'; // Medium - Yellow
    return '#10B981'; // Low - Green
  };

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
        
        <div className="text-right">
          <div className="flex gap-2 justify-end mb-2">
            <Badge variant="outline">
              Total Leads: {stats.totalLeads}
            </Badge>
            <Badge variant="outline" className="bg-blue-50">
              With Competitors: {stats.withCompetitors}
            </Badge>
          </div>
          <div className="flex gap-2 justify-end">
            <Badge variant="default" className="bg-red-500">
              High: {stats.competitorRanges.high}
            </Badge>
            <Badge variant="default" className="bg-yellow-500">
              Med: {stats.competitorRanges.medium}
            </Badge>
            <Badge variant="default" className="bg-green-500">
              Low: {stats.competitorRanges.low}
            </Badge>
          </div>
          <div className="text-sm text-muted-foreground mt-2">
            Avg Distance: {stats.avgDistance.toFixed(0)}m
          </div>
          <div className="text-sm text-muted-foreground">
            Avg Competitors: {stats.avgCompetitors.toFixed(1)}
          </div>
        </div>
      </div>

      <div className="flex gap-4">
        <div className="w-3/4">
          <svg
            width={width}
            height={height}
            viewBox={`0 0 ${width} ${height}`}
            className="bg-background"
          >
            {/* Draw competition radius circles */}
            {transformedData.map((feature, i) => (
              <g key={`lead-${i}`}>
                {/* Search radius circle */}
                <circle
                  cx={feature.point.x}
                  cy={feature.point.y}
                  r={radius * scale / 1000}
                  fill="none"
                  stroke={getCompetitionColor(feature.properties.competitor_count)}
                  strokeWidth={1}
                  strokeDasharray="4 4"
                  opacity={0.3}
                />
                
                {/* Competitor connections */}
                {feature.competitors.map((comp, j) => (
                  <line
                    key={`connection-${j}`}
                    x1={feature.point.x}
                    y1={feature.point.y}
                    x2={comp.x}
                    y2={comp.y}
                    stroke={getCompetitionColor(feature.properties.competitor_count)}
                    strokeWidth={1}
                    opacity={0.5}
                  />
                ))}
                
                {/* Lead point */}
                <circle
                  cx={feature.point.x}
                  cy={feature.point.y}
                  r={6}
                  fill={getCompetitionColor(feature.properties.competitor_count)}
                  stroke="white"
                  strokeWidth={2}
                  className="cursor-pointer"
                  onClick={() => setSelectedLead(feature)}
                >
                  <title>
                    Lead {feature.properties.lead_id}
                    Competitors: {feature.properties.competitor_count}
                    Nearest: {feature.properties.nearest_distance?.toFixed(0)}m
                  </title>
                </circle>
                
                {/* Competitor points */}
                {feature.competitors.map((comp, j) => (
                  <circle
                    key={`competitor-${j}`}
                    cx={comp.x}
                    cy={comp.y}
                    r={4}
                    fill="gray"
                    opacity={0.6}
                  >
                    <title>
                      Distance: {comp.distance.toFixed(0)}m
                    </title>
                  </circle>
                ))}
              </g>
            ))}
            
            {/* Legend */}
            <g transform={`translate(${width - 120}, ${height - 100})`}>
              <rect width={100} height={80} fill="white" opacity={0.9} rx={4} />
              {[
                { label: 'High (>5)', color: '#EF4444' },
                { label: 'Medium (3-5)', color: '#F59E0B' },
                { label: 'Low (≤2)', color: '#10B981' }
              ].map((item, i) => (
                <g key={i} transform={`translate(10, ${10 + i * 25})`}>
                  <circle cx={8} cy={8} r={6} fill={item.color} />
                  <text x={20} y={12} fontSize={12} fill="currentColor">
                    {item.label}
                  </text>
                </g>
              ))}
            </g>
          </svg>
        </div>

        {/* Selected lead details */}
        <div className="w-1/4">
          {selectedLead ? (
            <div className="p-4 rounded-md bg-background">
              <h3 className="font-medium mb-2">Lead Details</h3>
              <div className="text-sm mb-1">
                ID: {selectedLead.properties.lead_id}
              </div>
              <div className="text-sm mb-1">
                Competitors: {selectedLead.properties.competitor_count}
              </div>
              <div className="text-sm mb-3">
                Nearest: {selectedLead.properties.nearest_distance?.toFixed(0)}m
              </div>
              
              <h4 className="font-medium text-sm mb-2">Competitor Distances</h4>
              <div className="space-y-1">
                {selectedLead.properties.competitors.map((comp, i) => (
                  <div key={i} className="text-xs text-muted-foreground">
                    {comp.distance.toFixed(0)}m
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className="text-sm text-muted-foreground text-center mt-8">
              Select a lead to view details
            </div>
          )}
        </div>
      </div>
    </Card>
  );
};