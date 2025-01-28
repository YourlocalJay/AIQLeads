import React, { useMemo } from 'react';
import { Card } from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';

interface MarketFeature {
  type: 'Feature';
  properties: {
    area: string;
    penetration: number;
    total_leads: number;
    our_leads: number;
  };
}

interface MarketData {
  type: 'FeatureCollection';
  features: MarketFeature[];
}

interface MarketPenetrationMapProps {
  data: MarketData;
  width?: number;
  height?: number;
  subdivisionLevel?: 'district' | 'neighborhood' | 'zip_code';
  onSubdivisionChange?: (level: string) => void;
  className?: string;
}

export const MarketPenetrationMap: React.FC<MarketPenetrationMapProps> = ({
  data,
  width = 800,
  height = 600,
  subdivisionLevel = 'district',
  onSubdivisionChange,
  className = ''
}) => {
  // Calculate color scale
  const getColor = (penetration: number) => {
    // Blue scale from light to dark
    if (penetration >= 0.8) return '#1E40AF'; // dark blue
    if (penetration >= 0.6) return '#2563EB';
    if (penetration >= 0.4) return '#3B82F6';
    if (penetration >= 0.2) return '#60A5FA';
    return '#93C5FD'; // light blue
  };

  // Sort areas by penetration for the legend
  const sortedAreas = useMemo(() => {
    return [...data.features].sort((a, b) => b.properties.penetration - a.properties.penetration);
  }, [data]);

  // Calculate total market statistics
  const marketStats = useMemo(() => {
    const totalLeads = data.features.reduce((sum, f) => sum + f.properties.total_leads, 0);
    const ourLeads = data.features.reduce((sum, f) => sum + f.properties.our_leads, 0);
    const avgPenetration = ourLeads / totalLeads || 0;
    
    const penetrationDistribution = {
      high: data.features.filter(f => f.properties.penetration >= 0.6).length,
      medium: data.features.filter(f => f.properties.penetration >= 0.3 && f.properties.penetration < 0.6).length,
      low: data.features.filter(f => f.properties.penetration < 0.3).length
    };
    
    return {
      totalLeads,
      ourLeads,
      avgPenetration,
      penetrationDistribution
    };
  }, [data]);

  return (
    <Card className={`p-4 ${className}`}>
      <div className="flex justify-between items-start mb-4">
        <div>
          <Label>Subdivision Level</Label>
          <Select
            value={subdivisionLevel}
            onValueChange={onSubdivisionChange}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Select level" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="district">District</SelectItem>
              <SelectItem value="neighborhood">Neighborhood</SelectItem>
              <SelectItem value="zip_code">ZIP Code</SelectItem>
            </SelectContent>
          </Select>
        </div>
        
        <div className="text-right">
          <div className="text-sm font-medium">Market Overview</div>
          <div className="text-sm text-muted-foreground">
            Total Leads: {marketStats.totalLeads.toLocaleString()}
          </div>
          <div className="text-sm text-muted-foreground">
            Market Share: {(marketStats.avgPenetration * 100).toFixed(1)}%
          </div>
          <div className="flex gap-2 mt-2">
            <Badge variant="default" className="bg-blue-800">
              High: {marketStats.penetrationDistribution.high}
            </Badge>
            <Badge variant="default" className="bg-blue-600">
              Med: {marketStats.penetrationDistribution.medium}
            </Badge>
            <Badge variant="default" className="bg-blue-400">
              Low: {marketStats.penetrationDistribution.low}
            </Badge>
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
            {/* Market areas would be rendered here using a mapping service */}
            {/* For now, we'll show a grid representation */}
            {sortedAreas.map((feature, i) => {
              const row = Math.floor(i / 4);
              const col = i % 4;
              const size = Math.min(width / 4, height / 4) - 10;
              
              return (
                <g
                  key={feature.properties.area}
                  transform={`translate(${col * (size + 10) + 5}, ${row * (size + 10) + 5})`}
                >
                  <rect
                    width={size}
                    height={size}
                    fill={getColor(feature.properties.penetration)}
                    rx={4}
                  />
                  <text
                    x={size / 2}
                    y={size / 2 - 8}
                    textAnchor="middle"
                    fill="white"
                    fontSize={12}
                    fontWeight="bold"
                  >
                    {feature.properties.area}
                  </text>
                  <text
                    x={size / 2}
                    y={size / 2 + 8}
                    textAnchor="middle"
                    fill="white"
                    fontSize={10}
                  >
                    {(feature.properties.penetration * 100).toFixed(1)}%
                  </text>
                  <text
                    x={size / 2}
                    y={size / 2 + 24}
                    textAnchor="middle"
                    fill="white"
                    fontSize={10}
                  >
                    ({feature.properties.our_leads} / {feature.properties.total_leads})
                  </text>
                </g>
              );
            })}
            
            {/* Legend */}
            <g transform={`translate(${width - 120}, ${height - 150})`}>
              <rect width={100} height={130} fill="white" opacity={0.9} rx={4} />
              {[0.8, 0.6, 0.4, 0.2, 0].map((threshold, i) => (
                <g key={threshold} transform={`translate(10, ${10 + i * 25})`}>
                  <rect
                    width={20}
                    height={20}
                    fill={getColor(threshold)}
                  />
                  <text x={30} y={15} fontSize={12} fill="currentColor">
                    {threshold * 100}%+
                  </text>
                </g>
              ))}
            </g>
          </svg>
        </div>

        <div className="w-1/4">
          <div className="text-sm font-medium mb-2">Top Performing Areas</div>
          {sortedAreas.slice(0, 5).map(feature => (
            <div
              key={feature.properties.area}
              className="p-2 rounded-md mb-2"
              style={{ backgroundColor: `${getColor(feature.properties.penetration)}20` }}
            >
              <div className="font-medium">{feature.properties.area}</div>
              <div className="text-sm">
                Market Share: {(feature.properties.penetration * 100).toFixed(1)}%
              </div>
              <div className="text-xs text-muted-foreground">
                {feature.properties.our_leads} of {feature.properties.total_leads} leads
              </div>
            </div>
          ))}
        </div>
      </div>
    </Card>
  );
};