import React from 'react';
import { StudentFeatures } from '@shared/types';
import { BENCHMARKS } from '@shared/constants';
import { CheckCircle2, AlertTriangle } from 'lucide-react';

interface RadarProps {
  features: StudentFeatures;
}

interface Dimension {
  title: string;
  subTitle: string;
  studentScore: number; // 0 to 1
  benchmarkScore: number; // 0 to 1
  rawStudent: string;
  rawBenchmark: string;
  unit: string;
}

export const RadarCompetencyChart: React.FC<RadarProps> = ({ features }) => {
  // 6 Core dimensions normalized to 0..1 scale
  const dimensions: Dimension[] = [
    {
      title: 'Độ chuyên cần',
      subTitle: 'Số ngày học tích lũy',
      studentScore: Math.min(1, Math.max(0, features.active_days_to_t / 100)),
      benchmarkScore: Math.min(1, BENCHMARKS.active_days_to_t / 100),
      rawStudent: `${features.active_days_to_t}`,
      rawBenchmark: `${BENCHMARKS.active_days_to_t}`,
      unit: 'ngày',
    },
    {
      title: 'Tổng tương tác',
      subTitle: 'Lượt click VLE tích lũy',
      studentScore: Math.min(1, Math.max(0, features.total_clicks_to_t / 3000)),
      benchmarkScore: Math.min(1, BENCHMARKS.total_clicks_to_t / 3000),
      rawStudent: `${features.total_clicks_to_t}`,
      rawBenchmark: `${BENCHMARKS.total_clicks_to_t}`,
      unit: 'clicks',
    },
    {
      title: 'Tương tác gần đây',
      subTitle: 'Lượt click trong 7 ngày',
      studentScore: Math.min(1, Math.max(0, features.clicks_recent_7 / 150)),
      benchmarkScore: Math.min(1, BENCHMARKS.clicks_recent_7 / 150),
      rawStudent: `${features.clicks_recent_7}`,
      rawBenchmark: `${BENCHMARKS.clicks_recent_7}`,
      unit: 'clicks',
    },
    {
      title: 'Tỷ lệ nộp bài',
      subTitle: 'Tiến độ hoàn thành bài tập',
      studentScore: Math.min(1, Math.max(0, features.submission_rate)),
      benchmarkScore: BENCHMARKS.submission_rate,
      rawStudent: `${(features.submission_rate * 100).toFixed(0)}%`,
      rawBenchmark: `${(BENCHMARKS.submission_rate * 100).toFixed(0)}%`,
      unit: '',
    },
    {
      title: 'Kỷ luật đúng hạn',
      subTitle: 'Mức độ nộp bài đúng hạn',
      studentScore: Math.max(0, 1 - features.late_submissions_to_t * 0.3),
      benchmarkScore: 0.95,
      rawStudent: `${features.late_submissions_to_t} bài trễ`,
      rawBenchmark: '0 bài trễ',
      unit: '',
    },
    {
      title: 'Tỷ lệ ngày học',
      subTitle: 'Mật độ học tập định kỳ',
      studentScore: Math.min(1, Math.max(0, features.active_day_ratio)),
      benchmarkScore: BENCHMARKS.active_day_ratio,
      rawStudent: `${(features.active_day_ratio * 100).toFixed(0)}%`,
      rawBenchmark: `${(BENCHMARKS.active_day_ratio * 100).toFixed(0)}%`,
      unit: '',
    },
  ];

  const totalPoints = dimensions.length;

  // ViewBox Geometry: Expanded to 520x440 with center (260, 220) to ensure ALL labels fit comfortably
  const viewWidth = 520;
  const viewHeight = 440;
  const center = { x: 260, y: 220 };
  const maxRadius = 115;

  // Concentric radar ring scale
  const gridLevels = [0.25, 0.5, 0.75, 1.0];

  // Calculate polygon points on radar
  const getCoordinates = (value: number, index: number): [number, number] => {
    // Top vertex is index 0 (-90 degrees)
    const angle = (Math.PI * 2 / totalPoints) * index - Math.PI / 2;
    const r = Math.max(0.04, Math.min(1, value)) * maxRadius;
    const x = center.x + r * Math.cos(angle);
    const y = center.y + r * Math.sin(angle);
    return [x, y];
  };

  const studentPolygon = dimensions
    .map((d, i) => getCoordinates(d.studentScore, i).join(','))
    .join(' ');

  const benchmarkPolygon = dimensions
    .map((d, i) => getCoordinates(d.benchmarkScore, i).join(','))
    .join(' ');

  // Dedicated label coordinate configuration per vertex to prevent any text overlapping
  const getLabelConfig = (index: number) => {
    switch (index) {
      case 0:
        // Top vertex (0: Độ chuyên cần)
        return {
          x: center.x,
          y: center.y - maxRadius - 28,
          anchor: 'middle' as const,
        };
      case 1:
        // Top-Right vertex (1: Tổng tương tác)
        return {
          x: center.x + maxRadius * Math.cos(-Math.PI / 6) + 18,
          y: center.y + maxRadius * Math.sin(-Math.PI / 6) - 10,
          anchor: 'start' as const,
        };
      case 2:
        // Bottom-Right vertex (2: Tương tác gần đây)
        return {
          x: center.x + maxRadius * Math.cos(Math.PI / 6) + 18,
          y: center.y + maxRadius * Math.sin(Math.PI / 6) + 10,
          anchor: 'start' as const,
        };
      case 3:
        // Bottom vertex (3: Tỷ lệ nộp bài)
        return {
          x: center.x,
          y: center.y + maxRadius + 32,
          anchor: 'middle' as const,
        };
      case 4:
        // Bottom-Left vertex (4: Kỷ luật đúng hạn)
        return {
          x: center.x - maxRadius * Math.cos(Math.PI / 6) - 18,
          y: center.y + maxRadius * Math.sin(Math.PI / 6) + 10,
          anchor: 'end' as const,
        };
      case 5:
        // Top-Left vertex (5: Tỷ lệ ngày học)
        return {
          x: center.x - maxRadius * Math.cos(-Math.PI / 6) - 18,
          y: center.y + maxRadius * Math.sin(-Math.PI / 6) - 10,
          anchor: 'end' as const,
        };
      default:
        return { x: center.x, y: center.y, anchor: 'middle' as const };
    }
  };

  return (
    <div className="bg-slate-900/90 rounded-2xl border border-slate-800 shadow-xl p-5 sm:p-6">
      {/* Header & Legend */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6 pb-4 border-b border-slate-800">
        <div>
          <h3 className="text-base font-bold text-white flex items-center gap-2">
            <span>Đối sánh Năng lực &amp; Hành vi Học tập</span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-emerald-400 font-semibold">
              Radar 6D
            </span>
          </h3>
          <p className="text-xs text-slate-400 mt-0.5">
            So sánh dữ liệu thời gian thực của sinh viên với ngưỡng chuẩn Top 25% (OULAD Benchmark)
          </p>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 text-xs font-medium">
          <div className="flex items-center gap-2 px-2.5 py-1 rounded-lg bg-emerald-950/40 border border-emerald-500/30 text-emerald-300">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-400" />
            <span>Sinh viên hiện tại</span>
          </div>
          <div className="flex items-center gap-2 px-2.5 py-1 rounded-lg bg-blue-950/40 border border-blue-500/30 text-blue-300">
            <span className="w-2.5 h-2.5 rounded-full border border-blue-400 border-dashed bg-blue-400/30" />
            <span>Ngưỡng chuẩn (Giỏi)</span>
          </div>
        </div>
      </div>

      {/* Main Container: Radar chart on left, Breakdown table on right */}
      <div className="flex flex-col lg:flex-row items-center lg:items-stretch justify-between gap-8">
        
        {/* SVG Radar Container: dedicated width with full viewBox room */}
        <div className="w-full lg:w-[480px] xl:w-[500px] shrink-0 flex items-center justify-center p-2 rounded-2xl bg-slate-950/40 border border-slate-800/60">
          <svg
            viewBox={`0 0 ${viewWidth} ${viewHeight}`}
            className="w-full h-auto select-none"
            style={{ maxHeight: '420px' }}
          >
            {/* Concentric Polygons */}
            {gridLevels.map((lvl) => {
              const polyPoints = Array.from({ length: totalPoints })
                .map((_, i) => getCoordinates(lvl, i).join(','))
                .join(' ');
              return (
                <g key={lvl}>
                  <polygon
                    points={polyPoints}
                    fill={lvl === 1 ? 'rgba(15, 23, 42, 0.4)' : 'none'}
                    stroke="#1e293b"
                    strokeWidth="1.2"
                    strokeDasharray={lvl === 1 ? 'none' : '3,3'}
                  />
                  {/* Axis scale label on top vertical axis */}
                  <text
                    x={center.x + 4}
                    y={center.y - lvl * maxRadius - 2}
                    className="fill-slate-600 text-[9px] font-mono select-none"
                    textAnchor="start"
                  >
                    {`${lvl * 100}%`}
                  </text>
                </g>
              );
            })}

            {/* Axis Lines from Center to Vertices */}
            {dimensions.map((_, i) => {
              const [x, y] = getCoordinates(1, i);
              return (
                <line
                  key={i}
                  x1={center.x}
                  y1={center.y}
                  x2={x}
                  y2={y}
                  stroke="#334155"
                  strokeWidth="1"
                  strokeDasharray="2,2"
                />
              );
            })}

            {/* Benchmark Polygon */}
            <polygon
              points={benchmarkPolygon}
              fill="rgba(59, 130, 246, 0.12)"
              stroke="#60a5fa"
              strokeWidth="2"
              strokeDasharray="5,4"
            />

            {/* Student Polygon */}
            <polygon
              points={studentPolygon}
              fill="rgba(16, 185, 129, 0.22)"
              stroke="#10b981"
              strokeWidth="2.5"
            />

            {/* Student Vertex Dots */}
            {dimensions.map((d, i) => {
              const [sx, sy] = getCoordinates(d.studentScore, i);
              return (
                <g key={i}>
                  <circle
                    cx={sx}
                    cy={sy}
                    r="5"
                    fill="#10b981"
                    stroke="#0f172a"
                    strokeWidth="2"
                  />
                  <circle
                    cx={sx}
                    cy={sy}
                    r="2"
                    fill="#ffffff"
                  />
                </g>
              );
            })}

            {/* Dimension Labels (Multi-line and cleanly placed to prevent overlapping) */}
            {dimensions.map((d, i) => {
              const cfg = getLabelConfig(i);
              const isLagging = d.studentScore < d.benchmarkScore * 0.7;

              return (
                <g key={d.title} transform={`translate(${cfg.x}, ${cfg.y})`}>
                  {/* Title line */}
                  <text
                    x={0}
                    y={0}
                    textAnchor={cfg.anchor}
                    className="fill-slate-200 text-[11px] font-bold"
                  >
                    {d.title}
                  </text>

                  {/* Subtitle / metric value line */}
                  <text
                    x={0}
                    y={14}
                    textAnchor={cfg.anchor}
                    className={`text-[10px] font-mono font-medium ${
                      isLagging ? 'fill-rose-400' : 'fill-emerald-400'
                    }`}
                  >
                    {d.rawStudent} {d.unit}
                    <tspan className="fill-slate-500 font-sans">
                      {' '}(Chuẩn: {d.rawBenchmark})
                    </tspan>
                  </text>
                </g>
              );
            })}
          </svg>
        </div>

        {/* Dimension Breakdown Table on Right */}
        <div className="w-full lg:flex-1 flex flex-col justify-between space-y-2.5">
          <div className="text-xs font-semibold text-slate-300 pb-1 flex items-center justify-between">
            <span>Chi tiết từng tiêu chí quan trắc:</span>
            <span className="text-[11px] text-slate-400">Sinh viên / Chuẩn Giỏi</span>
          </div>

          {dimensions.map((dim) => {
            const isLagging = dim.studentScore < dim.benchmarkScore * 0.7;
            const progressPercent = Math.min(100, Math.round(dim.studentScore * 100));
            const benchmarkPercent = Math.min(100, Math.round(dim.benchmarkScore * 100));

            return (
              <div
                key={dim.title}
                className="p-3 rounded-xl bg-slate-950/60 border border-slate-800/80 hover:border-slate-700 transition-colors space-y-1.5"
              >
                <div className="flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2">
                    {isLagging ? (
                      <AlertTriangle className="w-3.5 h-3.5 text-rose-400 shrink-0" />
                    ) : (
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-400 shrink-0" />
                    )}
                    <span className="font-semibold text-slate-200">{dim.title}</span>
                    <span className="text-[10px] text-slate-400 hidden sm:inline">
                      ({dim.subTitle})
                    </span>
                  </div>

                  <div className="flex items-center gap-2 font-mono text-xs">
                    <span
                      className={`font-bold ${
                        isLagging ? 'text-rose-400' : 'text-emerald-400'
                      }`}
                    >
                      {dim.rawStudent} {dim.unit}
                    </span>
                    <span className="text-slate-600">/</span>
                    <span className="text-slate-400">
                      {dim.rawBenchmark} {dim.unit}
                    </span>
                  </div>
                </div>

                {/* Comparative Progress Bar */}
                <div className="h-1.5 w-full bg-slate-800 rounded-full overflow-hidden relative">
                  {/* Benchmark indicator tick */}
                  <div
                    className="absolute top-0 bottom-0 w-0.5 bg-blue-400 z-10"
                    style={{ left: `${benchmarkPercent}%` }}
                    title={`Ngưỡng chuẩn: ${benchmarkPercent}%`}
                  />
                  {/* Student actual progress */}
                  <div
                    className={`h-full rounded-full transition-all duration-500 ${
                      isLagging ? 'bg-rose-500' : 'bg-emerald-500'
                    }`}
                    style={{ width: `${progressPercent}%` }}
                  />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};
