import { useEffect, useMemo, useState } from 'react';
import ReactECharts from 'echarts-for-react';
import type { EChartsOption } from 'echarts';

export interface YoyData {
  quarters: string[];
  current_year: Record<string, number>;
  previous_year: Record<string, number>;
}

/** Grouped bar chart: this year's vs last year's quarterly surgery volumes. */
export function YoyAdherenceChart({ data, height = '100%' }: Readonly<{ data: YoyData | null; height?: string }>) {
  const isDark = useThemeDark();

  const option = useMemo<EChartsOption>(() => {
    const quarters = data?.quarters ?? ['Q1', 'Q2', 'Q3', 'Q4'];
    return {
      grid: { left: 48, right: 16, top: 32, bottom: 28 },
      tooltip: {
        trigger: 'axis',
        backgroundColor: isDark ? 'rgba(18,33,49,0.95)' : 'rgba(255,255,255,0.98)',
        borderColor: isDark ? '#3d4947' : '#e5e5e5',
        textStyle: { color: isDark ? '#d4e4fa' : '#1c1c1c', fontSize: 12 },
      },
      legend: {
        top: 0,
        right: 0,
        icon: 'roundRect',
        itemWidth: 12,
        itemHeight: 8,
        textStyle: { color: isDark ? '#cddbd8' : '#666666', fontSize: 11 },
      },
      xAxis: {
        type: 'category',
        data: quarters,
        axisLine: { lineStyle: { color: isDark ? '#3d4947' : '#eaeaea' } },
        axisTick: { show: false },
        axisLabel: { color: isDark ? '#879391' : '#666666', fontSize: 11 },
      },
      yAxis: {
        type: 'value',
        splitLine: { lineStyle: { color: isDark ? '#27364733' : '#00000008' } },
        axisLabel: { color: isDark ? '#879391' : '#999999', fontSize: 11 },
      },
      series: [
        {
          name: 'Previous year',
          type: 'bar',
          barMaxWidth: 22,
          itemStyle: { color: isDark ? '#3c4a5e' : '#d5e3fd', borderRadius: [4, 4, 0, 0] },
          data: quarters.map((q) => data?.previous_year?.[q] ?? 0),
        },
        {
          name: 'Current year',
          type: 'bar',
          barMaxWidth: 22,
          itemStyle: { color: isDark ? '#6bd8cb' : '#29a195', borderRadius: [4, 4, 0, 0] },
          data: quarters.map((q) => data?.current_year?.[q] ?? 0),
        },
      ],
    };
  }, [data, isDark]);

  return (
    <div style={{ height }} className="w-full">
      <ReactECharts option={option} notMerge style={{ width: '100%', height: '100%' }} opts={{ renderer: 'canvas' }} />
    </div>
  );
}

/** Track the current resolved theme so chart colors match. */
export function useThemeDark(): boolean {
  const [isDark, setIsDark] = useState(() => document.documentElement.classList.contains('dark'));
  useEffect(() => {
    const obs = new MutationObserver(() => {
      setIsDark(document.documentElement.classList.contains('dark'));
    });
    obs.observe(document.documentElement, { attributes: true, attributeFilter: ['class'] });
    return () => obs.disconnect();
  }, []);
  return isDark;
}
