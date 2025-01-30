import React, { useMemo, useState, useCallback } from 'react';
import { scaleQuantile } from 'd3-scale';
import { geoPath, geoMercator } from 'd3-geo';
import { FixedSizeGrid as Grid } from 'react-window';
import {
  Card,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Label,
  Badge,
  Tooltip,
  TooltipContent,
  TooltipTrigger,
  Slider,
  Button
} from '@/components/ui';

interface MarketFeature {
  type: 'Feature';
  geometry: {
    type: 'Polygon';
    coordinates: number[][][];
  };
  properties: {
    area: string;
    penetration: number;
    total_leads: number;
    our_leads: number;
    trend?: 'up' | 'down' | 'stable';
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
  onExport?: (format: 'png' | 'svg' | 'csv') => void;
}

export const MarketPenetrationMap: React.FC<MarketPenetrationMapProps> = ({
  data,
  width = 800,
  height = 600,
  subdivisionLevel = 'district',
  onSubdivisionChange,
  className = '',
  onExport
}) => {
  const [penetrationRange, setPenetrationRange] = useState<[number, number]>([0, 1]);
  const [viewMode, setViewMode] = useState<'grid' | 'map'>('grid');
  const [hoveredArea, setHoveredArea] = useState<string | null>(null);

  // Color scale setup
  const colorScale = useMemo(() => (
    scaleQuantile<string>()
      .domain(data.features.map(f => f.properties.penetration))
      .range(['#93C5FD', '#60A5FA', '#3B82F6', '#2563EB', '#1E40AF'])
  ), [data]);

  // Geographic projection
  const projection = useMemo(() => (
    geoMercator()
      .fitSize([width * 0.7, height], data)
      .precision(3)
  ), [data, width, height]);

  const pathGenerator = geoPath().projection(projection);

  // Filtered and sorted areas
  const filteredAreas = useMemo(() => (
    data.features
      .filter(f => f.properties.penetration >= penetrationRange[0] && 
                  f.properties.penetration <= penetrationRange[1])
      .sort((a, b) => b.properties.penetration - a.properties.penetration)
  ), [data, penetrationRange]);

  // Market statistics
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

  // Virtualized grid cell renderer
  const Cell = useCallback(({ columnIndex, rowIndex, style }) => {
    const index = rowIndex * 4 + columnIndex;
    const feature = filteredAreas[index];
    if (!feature) return null;

    const size = Math.min(width / 4, height / 4) - 10;
    
    return (
      <Tooltip key={feature.properties.area}>
        <TooltipTrigger asChild>
          <div style={style}>
            <svg width={size} height={size}>
              <rect
                width={size}
                height={size}
                fill={colorScale(feature.properties.penetration)}
                rx={4}
                onMouseEnter={() => setHoveredArea(feature.properties.area)}
                onMouseLeave={() => setHoveredArea(null)}
              />
              <text
                x={size / 2}
                y={size / 2}
                textAnchor="middle"
                fill="white"
                fontSize={12}
                fontWeight="bold"
              >
                {feature.properties.area}
              </text>
              {feature.properties.trend && (
                <svg x={size - 18} y={4} width={14} height={14}>
                  {feature.properties.trend === 'up' && (
                    <path d="M7 3L11 7M7 3L3 7" stroke="green" strokeWidth={2} />
                  )}
                  {feature.properties.trend === 'down' && (
                    <path d="M7 11L3 7M7 11L11 7" stroke="red" strokeWidth={2} />
                  )}
                </svg>
              )}
            </svg>
          </div>
        </TooltipTrigger>
        <TooltipContent>
          <p><strong>{feature.properties.area}</strong></p>
          <p>Market Share: {(feature.properties.penetration * 100).toFixed(1)}%</p>
          <p>Leads: {feature.properties.our_leads} / {feature.properties.total_leads}</p>
          {feature.properties.trend && (
            <p>Trend: {feature.properties.trend.charAt(0).toUpperCase() + feature.properties.trend.slice(1)}</p>
          )}
        </TooltipContent>
      </Tooltip>
    );
  }, [filteredAreas, width, height]);

  return (
    <Card className={`p-4 ${className}`}>
      <div className="flex justify-between items-start mb-4">
        <div className="flex gap-4">
          <div>
            <Label>Subdivision Level</Label>
            <Select value={subdivisionLevel} onValueChange={onSubdivisionChange}>
              <SelectTrigger aria-label="Select geographic subdivision level">
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
            <Label>View Mode</Label>
            <div className="flex gap-2">
              <Button
                variant={viewMode === 'grid' ? 'default' : 'outline'}
                onClick={() => setViewMode('grid')}
              >
                Grid
              </Button>
              <Button
                variant={viewMode === 'map' ? 'default' : 'outline'}
                onClick={() => setViewMode('map')}
              >
                Map
              </Button>
            </div>
          </div>
        </div>

        <div className="flex gap-4">
          <div>
            <Label>Penetration Range</Label>
            <Slider
              value={penetrationRange}
              onValueChange={setPenetrationRange}
              min={0}
              max={1}
              step={0.05}
              className="w-[180px]"
              aria-label="Penetration range filter"
              aria-valuetext={`From ${penetrationRange[0] * 100}% to ${penetrationRange[1] * 100}%`}
            />
            <div className="text-sm text-muted-foreground mt-1">
              {Math.round(penetrationRange[0] * 100)}% - {Math.round(penetrationRange[1] * 100)}%
            </div>
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
              <Badge className="bg-blue-800">High: {marketStats.penetrationDistribution.high}</Badge>
              <Badge className="bg-blue-600">Med: {marketStats.penetrationDistribution.medium}</Badge>
              <Badge className="bg-blue-400">Low: {marketStats.penetrationDistribution.low}</Badge>
            </div>
          </div>
        </div>
      </div>

      <div className="flex gap-4">
        <div className="w-3/4 relative">
          {viewMode === 'grid' ? (
            <Grid
              columnCount={4}
              rowCount={Math.ceil(filteredAreas.length / 4)}
              columnWidth={Math.min(width / 4, height / 4)}
              rowHeight={Math.min(width / 4, height / 4)}
              width={width * 0.7}
              height={height}
            >
              {Cell}
            </Grid>
          ) : (
            <svg width={width * 0.7} height={height}>
              {filteredAreas.map(feature => (
                <Tooltip key={feature.properties.area}>
                  <TooltipTrigger asChild>
                    <path
                      d={pathGenerator(feature.geometry)!}
                      fill={colorScale(feature.properties.penetration)}
                      stroke="#fff"
                      strokeWidth={0.5}
                      opacity={hoveredArea === feature.properties.area ? 0.8 : 1}
                      onMouseEnter={() => setHoveredArea(feature.properties.area)}
                      onMouseLeave={() => setHoveredArea(null)}
                    />
                  </TooltipTrigger>
                  <TooltipContent>
                    <p><strong>{feature.properties.area}</strong></p>
                    <p>Market Share: {(feature.properties.penetration * 100).toFixed(1)}%</p>
                    <p>Leads: {feature.properties.our_leads} / {feature.properties.total_leads}</p>
                  </TooltipContent>
                </Tooltip>
              ))}
            </svg>
          )}

          {/* Legend */}
          <div className="absolute bottom-4 right-4 bg-background p-4 rounded-lg shadow-sm">
            <div className="text-sm font-medium mb-2">Market Penetration</div>
            {colorScale.range().map((color, i) => (
              <div key={color} className="flex items-center gap-2 text-sm">
                <div
                  className="w-4 h-4 rounded-sm"
                  style={{ backgroundColor: color }}
                />
                <span>
                  {i === 0 ? '<20%' : 
                   i === colorScale.range().length - 1 ? '>80%' : 
                   `${i * 20}% - ${(i + 1) * 20}%`}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div className="w-1/4 pl-4">
          <div className="space-y-4">
            <div>
              <Label>Export Data</Label>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={() => onExport?.('png')}>
                  PNG
                </Button>
                <Button variant="outline" size="sm" onClick={() => onExport?.('svg')}>
                  SVG
                </Button>
                <Button variant="outline" size="sm" onClick={() => onExport?.('csv')}>
                  CSV
                </Button>
              </div>
            </div>

            <div>
              <Label>Benchmarks</Label>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between">
                  <span>Regional Average:</span>
                  <span>42.5%</span>
                </div>
                <div className="flex justify-between">
                  <span>National Average:</span>
                  <span>38.1%</span>
                </div>
              </div>
            </div>

            <div>
              <Label>Alerts</Label>
              <div className="space-y-2">
                {filteredAreas
                  .filter(f => f.properties.trend === 'down')
                  .map(feature => (
                    <div key={feature.properties.area} className="text-sm text-red-600">
                      ▼ {feature.properties.area} - Decreasing penetration
                    </div>
                  ))}
              </div>
            </div>
          </div>
        </div>
      </div>
    </Card>
  );
};
