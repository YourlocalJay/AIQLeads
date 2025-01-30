import React, { useMemo, useState, useEffect } from 'react';
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
import { Tooltip, TooltipContent, TooltipTrigger } from '@/components/ui/tooltip';
import { Slider } from '@/components/ui/slider';

interface MarketFeature {
  type: 'Feature';
  properties: {
    area: string;
    penetration: number;
    total_leads: number;
    our_leads: number;
    trend?: 'up' | 'down' | 'stable'; // Market penetration trend
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
  const [penetrationRange, setPenetrationRange] = useState<[number, number]>([0, 1]);

  // Generate color scale dynamically based on penetration
  const getColor = (penetration: number) => {
    const colors = ['#93C5FD', '#60A5FA', '#3B82F6', '#2563EB', '#1E40AF'];
    const thresholds = [0.2, 0.4, 0.6, 0.8];

    for (let i = 0; i < thresholds.length; i++) {
      if (penetration < thresholds[i]) return colors[i];
    }
    return colors[colors.length - 1];
  };

  // Sort and filter areas dynamically
  const filteredAreas = useMemo(() => {
    return data.features
      .filter(f => f.properties.penetration >= penetrationRange[0] && f.properties.penetration <= penetrationRange[1])
      .sort((a, b) => b.properties.penetration - a.properties.penetration);
  }, [data, penetrationRange]);

  // Calculate market statistics
  const marketStats = useMemo(() => {
    const totalLeads = data.features.reduce((sum, f) => sum + f.properties.total_leads, 0);
    const ourLeads = data.features.reduce((sum, f) => sum + f.properties.our_leads, 0);
    const avgPenetration = ourLeads / totalLeads || 0;

    return {
      totalLeads,
      ourLeads,
      avgPenetration,
      penetrationDistribution: {
        high: filteredAreas.filter(f => f.properties.penetration >= 0.6).length,
        medium: filteredAreas.filter(f => f.properties.penetration >= 0.3 && f.properties.penetration < 0.6).length,
        low: filteredAreas.filter(f => f.properties.penetration < 0.3).length
      }
    };
  }, [filteredAreas]);

  return (
    <Card className={`p-4 ${className}`}>
      <div className="flex justify-between items-start mb-4">
        <div>
          <Label>Subdivision Level</Label>
          <Select value={subdivisionLevel} onValueChange={onSubdivisionChange}>
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

        <div>
          <Label>Penetration Range</Label>
          <Slider
            value={penetrationRange}
            onValueChange={setPenetrationRange}
            min={0}
            max={1}
            step={0.05}
            className="w-[180px]"
          />
          <div className="text-sm text-muted-foreground mt-1">
            {Math.round(penetrationRange[0] * 100)}% - {Math.round(penetrationRange[1] * 100)}%
          </div>
        </div>

        <div className="text-right">
          <div className="text-sm font-medium">Market Overview</div>
          <div className="text-sm text-muted-foreground">Total Leads: {marketStats.totalLeads.toLocaleString()}</div>
          <div className="text-sm text-muted-foreground">Market Share: {(marketStats.avgPenetration * 100).toFixed(1)}%</div>
          <div className="flex gap-2 mt-2">
            <Badge className="bg-blue-800">High: {marketStats.penetrationDistribution.high}</Badge>
            <Badge className="bg-blue-600">Med: {marketStats.penetrationDistribution.medium}</Badge>
            <Badge className="bg-blue-400">Low: {marketStats.penetrationDistribution.low}</Badge>
          </div>
        </div>
      </div>

      <div className="flex gap-4">
        <div className="w-3/4">
          <svg width={width} height={height} className="bg-background">
            {filteredAreas.map((feature, i) => {
              const row = Math.floor(i / 4);
              const col = i % 4;
              const size = Math.min(width / 4, height / 4) - 10;

              return (
                <Tooltip key={feature.properties.area}>
                  <TooltipTrigger asChild>
                    <g transform={`translate(${col * (size + 10) + 5}, ${row * (size + 10) + 5})`}>
                      <rect width={size} height={size} fill={getColor(feature.properties.penetration)} rx={4} />
                      <text x={size / 2} y={size / 2} textAnchor="middle" fill="white" fontSize={12} fontWeight="bold">
                        {feature.properties.area}
                      </text>
                    </g>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p><strong>{feature.properties.area}</strong></p>
                    <p>Market Share: {(feature.properties.penetration * 100).toFixed(1)}%</p>
                    <p>Leads: {feature.properties.our_leads} of {feature.properties.total_leads}</p>
                  </TooltipContent>
                </Tooltip>
              );
            })}
          </svg>
        </div>
      </div>
    </Card>
  );
};
