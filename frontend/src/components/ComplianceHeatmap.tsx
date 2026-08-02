import { useEffect, useRef, useState } from 'react';
import ReactECharts from 'echarts-for-react';
import * as echarts from 'echarts';
import { publicApi } from '../services/api/public';

interface HeatmapState {
  state: string;
  centres: number;
  inspections: number;
  compliance_rate: number;
  risk: 'critical' | 'moderate' | 'compliant';
}

interface ComplianceHeatmapProps {
  className?: string;
  height?: string;
}

export function ComplianceHeatmap({ className = '', height = '400px' }: ComplianceHeatmapProps) {
  const [data, setData] = useState<HeatmapState[]>([]);
  const [loading, setLoading] = useState(true);
  const [mapReady, setMapReady] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const chartRef = useRef<ReactECharts>(null);

  useEffect(() => {
    const fetchHeatmap = async () => {
      try {
        const heatmapData = await publicApi.getHeatmap();
        setData(heatmapData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load heatmap');
      } finally {
        setLoading(false);
      }
    };

    fetchHeatmap();
  }, []);

  // Load India map dynamically
  useEffect(() => {
    const registerMap = async () => {
      try {
        // Dynamic import to avoid bundling 21.9 MB GeoJSON
        const geoJsonModule = await import('../assets/india-states.geojson?raw');
        const geoJson = JSON.parse(geoJsonModule.default);
        
        // GeoJSON uses NAME_1 as the state name property; ECharts matches regions by `name`
        const normalized = {
          ...geoJson,
          features: geoJson.features.map((f: any) => ({
            ...f,
            properties: { ...f.properties, name: f.properties.NAME_1 },
          })),
        };
        echarts.registerMap('india', normalized);
        setMapReady(true);
      } catch (err) {
        console.error('Failed to load India GeoJSON:', err);
        setError('Failed to load map data');
        setMapReady(false);
      }
    };
    registerMap();
  }, []);

  const ready = !loading && mapReady;

  if (!ready && !error) {
    return (
      <div className={`bg-surface-container-lowest border border-outline-variant/50 rounded flex items-center justify-center ${className}`} style={{ minHeight: height }}>
        <div className="flex flex-col items-center gap-3 text-on-surface-variant">
          <div className="w-8 h-8 border-3 border-primary border-t-transparent rounded-full animate-spin" />
          <span className="font-label-md">Loading compliance heatmap...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className={`bg-surface-container-lowest border border-outline-variant/50 rounded flex items-center justify-center ${className}`} style={{ minHeight: height }}>
        <div className="flex flex-col items-center gap-3 text-error p-4 text-center">
          <span className="material-symbols-outlined text-[48px]">error_outline</span>
          <span className="font-label-md">Failed to load heatmap</span>
          <span className="font-body-sm text-on-surface-variant max-w-xs">{error}</span>
        </div>
      </div>
    );
  }

  // Prepare ECharts data
  const mapData = data.map((d) => ({
    name: d.state,
    value: d.compliance_rate,
    centres: d.centres,
    inspections: d.inspections,
    risk: d.risk,
  }));

  const option = {
    tooltip: {
      trigger: 'item',
      backgroundColor: 'rgba(15, 23, 42, 0.95)',
      borderColor: 'rgba(148, 163, 184, 0.2)',
      borderWidth: 1,
      padding: 12,
      textStyle: { color: '#f8fafc' },
      formatter: (params: any) => {
        const item = params.data;
        const riskColors = { critical: '#ef4444', moderate: '#f59e0b', compliant: '#22c55e' };
        const riskLabel = item.risk?.charAt(0).toUpperCase() + item.risk?.slice(1) || 'Unknown';
        return `
          <div style="font-weight: 600; margin-bottom: 8px;">${item.name}</div>
          <div style="display: grid; grid-template-columns: auto 1fr; gap: 4px 12px; font-size: 13px;">
            <span style="color: #94a3b8;">Compliance:</span>
            <span style="color: ${riskColors[item.risk as keyof typeof riskColors] || '#64748b'}; font-weight: 500;">${item.value}%</span>
            <span style="color: #94a3b8;">Risk:</span>
            <span style="color: ${riskColors[item.risk as keyof typeof riskColors] || '#64748b'}; font-weight: 500;">${riskLabel}</span>
            <span style="color: #94a3b8;">Centres:</span>
            <span>${item.centres}</span>
            <span style="color: #94a3b8;">Inspections:</span>
            <span>${item.inspections}</span>
          </div>
        `;
      },
    },
    visualMap: {
      type: 'continuous',
      min: 0,
      max: 100,
      calculable: true,
      orient: 'horizontal',
      left: 'center',
      bottom: 10,
      inRange: {
        color: ['#ef4444', '#f59e0b', '#22c55e'],
      },
      text: ['Critical', 'Compliant'],
      textStyle: { color: '#94a3b8', fontSize: 11 },
      itemWidth: 20,
      itemHeight: 180,
    },
    geo: {
      map: 'india',
      roam: true,
      zoom: 1.2,
      center: [78.96, 20.59],
      label: {
        show: true,
        color: '#94a3b8',
        fontSize: 10,
        fontWeight: 400,
      },
      itemStyle: {
        areaColor: 'rgba(30, 41, 59, 0.8)',
        borderColor: '#334155',
        borderWidth: 1,
      },
      emphasis: {
        label: { color: '#f8fafc', fontSize: 11, fontWeight: 500 },
        itemStyle: { areaColor: 'rgba(51, 65, 85, 0.9)', borderWidth: 2 },
      },
    },
    series: [
      {
        name: 'Compliance Rate',
        type: 'map',
        map: 'india',
        data: mapData,
        label: { show: false },
        emphasis: { label: { show: true } },
      },
    ],
  };

  const legendItems = [
    { color: 'bg-error', label: 'Critical (< 50%)' },
    { color: 'bg-secondary', label: 'Moderate (50-79%)' },
    { color: 'bg-primary', label: 'Compliant (80%+)' },
  ];

  return (
    <div className={`relative overflow-hidden rounded-lg border border-outline-variant bg-background ${className}`} style={{ height }}>
      <ReactECharts
        ref={chartRef}
        option={option}
        style={{ width: '100%', height: '100%' }}
        opts={{ renderer: 'canvas' }}
      />
      {/* Legend overlay */}
      <div className="absolute bottom-3 left-3 bg-surface/90 backdrop-blur-sm border border-outline-variant p-2 rounded text-xs space-y-1">
        {legendItems.map((item, idx) => (
          <div key={idx} className="flex items-center gap-2">
            <div className={`w-2 h-2 ${item.color} rounded-full`}></div>
            <span className="text-on-surface-variant">{item.label}</span>
          </div>
        ))}
      </div>
    </div>
  );
}