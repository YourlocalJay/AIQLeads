import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Loader } from 'lucide-react';

type VisualizationType = 'heatmap' | 'clusters' | 'choropleth' | 'competitors';

interface GeoJSONFeature {
  type: 'Feature';
  geometry: {
    type: string;
    coordinates: number[][];
  };
  properties: Record<string, any>;
}

interface GeoJSONResponse {
  type: 'FeatureCollection';
  features: GeoJSONFeature[];
}

interface GeospatialMapProps {
  region: string;
  initialType?: VisualizationType;
  onDataLoad?: (data: GeoJSONResponse) => void;
  onError?: (error: Error) => void;
  className?: string;
}

export const GeospatialMap: React.FC<GeospatialMapProps> = ({
  region,
  initialType = 'heatmap',
  onDataLoad,
  onError,
  className = ''
}) => {
  const [visualizationType, setVisualizationType] = useState<VisualizationType>(initialType);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [data, setData] = useState<GeoJSONResponse | null>(null);

  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      setError(null);
      
      try {
        const response = await fetch(`/api/geospatial/${visualizationType}?region=${region}`);
        if (!response.ok) {
          throw new Error(`Failed to fetch ${visualizationType} data`);
        }
        
        const jsonData: GeoJSONResponse = await response.json();
        setData(jsonData);
        onDataLoad?.(jsonData);
      } catch (err) {
        const errorMessage = err instanceof Error ? err.message : 'Failed to load data';
        setError(errorMessage);
        onError?.(err as Error);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [region, visualizationType, onDataLoad, onError]);

  return (
    <Card className={`w-full ${className}`}>
      <CardHeader>
        <div className="flex justify-between items-center">
          <div>
            <CardTitle>Geospatial Analysis</CardTitle>
            <CardDescription>
              {region} Region - {visualizationType.charAt(0).toUpperCase() + visualizationType.slice(1)} View
            </CardDescription>
          </div>
          <Select
            value={visualizationType}
            onValueChange={(value) => setVisualizationType(value as VisualizationType)}
          >
            <SelectTrigger className="w-[180px]">
              <SelectValue placeholder="Select view" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="heatmap">Lead Density</SelectItem>
              <SelectItem value="clusters">Clusters</SelectItem>
              <SelectItem value="choropleth">Market Share</SelectItem>
              <SelectItem value="competitors">Competitors</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardHeader>
      <CardContent>
        <div className="h-96 relative">
          {loading ? (
            <div className="absolute inset-0 flex items-center justify-center bg-background/50">
              <Loader className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : error ? (
            <div className="absolute inset-0 flex items-center justify-center text-destructive">
              {error}
            </div>
          ) : data ? (
            <div className="h-full">
              {/* Map implementation will be added here */}
              <pre className="overflow-auto h-full">
                {JSON.stringify(data, null, 2)}
              </pre>
            </div>
          ) : null}
        </div>
      </CardContent>
    </Card>
  );
};