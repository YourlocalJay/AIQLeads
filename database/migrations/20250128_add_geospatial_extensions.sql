-- Enable PostGIS extension if not already enabled
CREATE EXTENSION IF NOT EXISTS postgis;

-- Add geometry columns to markets table
ALTER TABLE markets 
    ADD COLUMN center_point geometry(Point, 4326),
    ADD COLUMN boundary geometry(MultiPolygon, 4326);

-- Add geometry column to leads table for location
ALTER TABLE leads
    ADD COLUMN location geometry(Point, 4326);

-- Create generated column to automatically update location from lat/long
ALTER TABLE leads
    ADD COLUMN geom_location geometry(Point, 4326) 
    GENERATED ALWAYS AS (
        ST_SetSRID(ST_MakePoint(longitude, latitude), 4326)
    ) STORED;

-- Create spatial indexes
CREATE INDEX idx_market_center_point 
    ON markets USING GIST (center_point);
CREATE INDEX idx_market_boundary 
    ON markets USING GIST (boundary);
CREATE INDEX idx_leads_location 
    ON leads USING GIST (geom_location);

-- Create function to calculate distance in kilometers
CREATE OR REPLACE FUNCTION calculate_distance_km(
    point1 geometry,
    point2 geometry
) RETURNS float AS $$
BEGIN
    RETURN ST_Distance(
        point1::geography,
        point2::geography
    ) / 1000.0;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Create function to calculate area density
CREATE OR REPLACE FUNCTION calculate_area_density(
    center_point geometry,
    radius_km float,
    OUT lead_count integer,
    OUT density float
) AS $$
DECLARE
    search_area geometry;
    area_size float;
BEGIN
    -- Create search area
    search_area := ST_Buffer(
        center_point::geography,
        radius_km * 1000.0
    )::geometry;
    
    -- Count leads in area
    SELECT COUNT(*) INTO lead_count
    FROM leads
    WHERE ST_Within(geom_location, search_area);
    
    -- Calculate area in square km
    area_size := ST_Area(search_area::geography) / 1000000.0;
    
    -- Calculate density
    density := CASE 
        WHEN area_size > 0 THEN lead_count::float / area_size
        ELSE 0.0
    END;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- Create materialized view for market statistics
CREATE MATERIALIZED VIEW market_stats AS
SELECT 
    m.id AS market_id,
    ST_Area(m.boundary::geography) / 1000000.0 AS area_sq_km,
    COUNT(l.id) AS total_leads,
    COUNT(l.id)::float / (ST_Area(m.boundary::geography) / 1000000.0) AS lead_density
FROM markets m
LEFT JOIN leads l ON ST_Within(l.geom_location, m.boundary)
GROUP BY m.id, m.boundary;

CREATE UNIQUE INDEX idx_market_stats_id ON market_stats(market_id);

-- Create refresh function for market_stats
CREATE OR REPLACE FUNCTION refresh_market_stats()
RETURNS trigger AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY market_stats;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to refresh stats when leads change
CREATE TRIGGER refresh_market_stats_trigger
AFTER INSERT OR UPDATE OR DELETE ON leads
FOR EACH STATEMENT
EXECUTE FUNCTION refresh_market_stats();