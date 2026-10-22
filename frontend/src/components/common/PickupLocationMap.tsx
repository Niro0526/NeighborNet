import React, { useEffect, useRef, useState } from 'react';
import * as maplibregl from 'maplibre-gl';
import mapWorkerUrl from 'maplibre-gl/dist/maplibre-gl-worker.mjs?url';
import 'maplibre-gl/dist/maplibre-gl.css';

maplibregl.setWorkerUrl(mapWorkerUrl);

interface PickupLocationMapProps {
  latitude: number;
  longitude: number;
  onChange: (latitude: number, longitude: number) => void;
}

const MAP_STYLE = {
  version: 8,
  sources: {
    osm: {
      type: 'raster',
      tiles: ['https://tile.openstreetmap.org/{z}/{x}/{y}.png'],
      tileSize: 256,
      attribution: '&copy; OpenStreetMap contributors',
    },
  },
  layers: [{ id: 'osm', type: 'raster', source: 'osm' }],
};

export const PickupLocationMap: React.FC<PickupLocationMapProps> = ({ latitude, longitude, onChange }) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const markerRef = useRef<maplibregl.Marker | null>(null);
  const [locationMessage, setLocationMessage] = useState<string | null>(null);

  useEffect(() => {
    if (!containerRef.current) return;
    const map = new maplibregl.Map({
      container: containerRef.current,
      style: MAP_STYLE as maplibregl.StyleSpecification,
      center: [longitude, latitude],
      zoom: 12,
    });
    map.addControl(new maplibregl.NavigationControl(), 'top-right');
    const marker = new maplibregl.Marker({ draggable: true, color: '#16866A' })
      .setLngLat([longitude, latitude])
      .addTo(map);
    marker.on('dragend', () => {
      const position = marker.getLngLat();
      onChange(position.lat, position.lng);
    });
    map.on('click', (event: maplibregl.MapMouseEvent) => {
      marker.setLngLat(event.lngLat);
      onChange(event.lngLat.lat, event.lngLat.lng);
    });
    mapRef.current = map;
    markerRef.current = marker;
    return () => {
      marker.remove();
      map.remove();
      mapRef.current = null;
      markerRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    const marker = markerRef.current;
    if (!map || !marker) return;
    marker.setLngLat([longitude, latitude]);
    map.easeTo({ center: [longitude, latitude], duration: 300 });
  }, [latitude, longitude]);

  const detectLocation = () => {
    if (!navigator.geolocation) {
      setLocationMessage('GPS is not available in this browser. Select the pin manually.');
      return;
    }
    setLocationMessage('Requesting your location...');
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => {
        onChange(coords.latitude, coords.longitude);
        setLocationMessage(`GPS location detected (accuracy ±${Math.round(coords.accuracy)}m).`);
      },
      () => setLocationMessage('Location access was denied. Enter the address or drag the pin manually.'),
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 },
    );
  };

  return (
    <div className="space-y-2">
      <div ref={containerRef} className="h-64 w-full overflow-hidden rounded-xl border border-[#E5EAE7]" />
      <div className="flex flex-wrap items-center justify-between gap-2">
        <p className="text-[11px] text-[#64748B]">Drag the pin or click the map to set the pickup point.</p>
        <button type="button" onClick={detectLocation} className="rounded-lg border border-[#E5EAE7] px-3 py-1.5 text-[11px] font-bold text-[#16866A] hover:bg-emerald-50">
          Use my GPS location
        </button>
      </div>
      {locationMessage && <p className="text-[11px] text-[#64748B]">{locationMessage}</p>}
    </div>
  );
};
