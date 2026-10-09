import React from 'react';
import { StudentFeatures } from '@shared/types';
import { BENCHMARKS } from '@shared/constants';

interface RadarProps {
  features: StudentFeatures;
}

interface Dimension {
  label: string;
  studentScore: number; // 0 to 1
  benchmarkScore: number; // 0 to 1
  rawStudent: string;
  rawBenchmark: string;
}

export const RadarCompetencyChart: React.FC<RadarProps> = ({ features }) => {
  // Normalize each metric to 0..1 scale
  const dimensions: Dimension[] = [
    {
      label: 'Độ chuyên cần',
      studentScore: Math.min(1, Math.max(0, features.active_days_to_t / 100)),
      benchmarkScore: Math.min(1, BENCHMARKS.active_days_to_t / 100),
      rawStudent: `${features.active_days_to_t} ngày`,
      rawBenchmark: `${BENCHMARKS.active_days_to_t} ngày`,
    },
    {
      label: 'Tổng lượt tương tác',
      studentScore: Math.min(1, Math.max(0, features.total_clicks_to_t / 3000)),
      benchmarkScore: Math.min(1, BENCHMARKS.total_clicks_to_t / 3000),
      rawStudent: `${features.total_clicks_to_t} clicks`,
      rawBenchmark: `${BENCHMARKS.total_clicks_to_t} clicks`,
    },
    {
      label: 'Tương tác 7 ngày gần nhất',
      studentScore: Math.min(1, Math.max(0, features.clicks_recent_7 / 150)),
      benchmarkScore: Math.min(1, BENCHMARKS.clicks_recent_7 / 150),
      rawStudent: `${features.clicks_recent_7} clicks`,
      rawBenchmark: `${BENCHMARKS.clicks_recent_7} clicks`,
    },
    {
      label: 'Tỷ lệ nộp bài',
      studentScore: Math.min(1, Math.max(0, features.submission_rate)),
      benchmarkScore: BENCHMARKS.submission_rate,
      rawStudent: `${(features.submission_rate * 100).toFixed(0)}%`,
      rawBenchmark: `${(BENCHMARKS.submission_rate * 100).toFixed(0)}%`,
    },
    {
      label: 'Kỷ luật đúng hạn',
      studentScore: Math.max(0, 1 - features.late_submissions_to_t * 0.3),
      benchmarkScore: 0.95,
      rawStudent: `${features.late_submissions_to_t} trễ`,
      rawBenchmark: `≤ 0 bài`,
    },
    {
      label: 'Tỷ lệ ngày học',
      studentScore: Math.min(1, Math.max(0, features.active_day_ratio)),
      benchmarkScore: BENCHMARKS.active_day_ratio,
      rawStudent: `${(features.active_day_ratio * 100).toFixed(0)}%`,
      rawBenchmark: `${(BENCHMARKS.active_day_ratio * 100).toFixed(0)}%`,
    },
  ];

  const totalPoints = dimensions.length;
  const size = 300;
  const center = size / 2;
  const maxRadius = 100;

  // Calculate polygon points
  const getCoordinates = (value: number, index: number): [number, number] => {
    const angle = (Math.PI * 2 / totalPoints) * index - Math.PI / 2;
    const r = value * maxRadius;
    const x = center + r * Math.cos(angle);
    const y = center + r * Math.sin(angle);
    return [x, y];
  };

  const studentPolygon = dimensions
    .map((d, i) => getCoordinates(d.studentScore, i).join(','))
    .join(' ');

  const benchmarkPolygon = dimensions
    .map((d, i) => getCoordinates(d.benchmarkScore, i).join(','))
    .join(' ');

  // Grid concentric rings (0.25, 0.5, 0.75, 1.0)
  const gridLevels = [0.25, 0.5, 0.75, 1.0];

  return (
    <div className="bg-slate-900/90 rounded-2xl border border-slate-800 shadow-xl p-5 sm:p-6">
      <div className="flex items-center justify-between mb-2">
        <div>
          <h3 className="text-base font-bold text-white">Đối sánh Năng lực & Hành vi</h3>
          <p className="text-xs text-slate-400">So sánh với ngưỡng trung vị sinh viên Giỏi (OULAD)</p>
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 text-xs font-medium">
          <div className="flex items-center gap-1.5 text-emerald-400">
            <span className="w-3 h-3 rounded-full bg-emerald-500/30 border border-emerald-400" />
            <span>Sinh viên hiện tại</span>
          </div>
          <div className="flex items-center gap-1.5 text-blue-400">
            <span className="w-3 h-3 rounded-full bg-blue-500/20 border border-blue-400 border-dashed" />
            <span>Chuẩn Benchmark</span>
          </div>
        </div>
      </div>

      <div className="flex flex-col md:flex-row items-center justify-center gap-6">
        {/* SVG Radar */}
        <div className="w-full max-w-[320px] aspect-square relative">
          <svg viewBox={`0 0 ${size} ${size}`} className="w-full h-full overflow-visible">
            {/* Concentric rings */}
            {gridLevels.map((lvl) => {
              const polyPoints = Array.from({ length: totalPoints })
                .map((_, i) => getCoordinates(lvl, i).join(','))
                .join(' ');
              return (
                <polygon
                  key={lvl}
                  points={polyPoints}
                  fill="none"
                  stroke="#1e293b"
                  strokeWidth="1"
                  strokeDasharray={lvl === 1 ? 'none' : '2,2'}
                />
              );
            })}

            {/* Axis lines */}
            {dimensions.map((_, i) => {
              const [x, y] = getCoordinates(1, i);
              return (
                <line
                  key={i}
                  x1={center}
                  y1={center}
                  x2={x}
                  y2={y}
                  stroke="#334155"
                  strokeWidth="1"
                />
              );
            })}

            {/* Benchmark polygon */}
            <polygon
              points={benchmarkPolygon}
              fill="rgba(59, 130, 246, 0.15)"
              stroke="#60a5fa"
              strokeWidth="2"
              strokeDasharray="4,3"
            />

            {/* Student polygon */}
            <polygon
              points={studentPolygon}
              fill="rgba(16, 185, 129, 0.25)"
              stroke="#10b981"
              strokeWidth="2.5"
            />

            {/* Vertex points */}
            {dimensions.map((d, i) => {
              const [sx, sy] = getCoordinates(d.studentScore, i);
              return (
                <circle
                  key={i}
                  cx={sx}
                  cy={sy}
                  r="4"
                  fill="#10b981"
                  stroke="#0f172a"
                  strokeWidth="1.5"
                />
              );
            })}

            {/* Dimension Labels */}
            {dimensions.map((d, i) => {
              const angle = (Math.PI * 2 / totalPoints) * indexToAngle(i) - Math.PI / 2;
              const labelRadius = maxRadius + 22;
              const lx = center + labelRadius * Math.cos(angle);
              const ly = center + labelRadius * Math.sin(angle);

              let textAnchor: 'middle' | 'start' | 'end' = 'middle';
              if (Math.cos(angle) > 0.3) textAnchor = 'start';
              else if (Math.cos(angle) < -0.3) textAnchor = 'end';

              return (
                <text
                  key={d.label}
                  x={lx}
                  y={ly}
                  textAnchor={textAnchor}
                  className="fill-slate-300 text-[10px] font-semibold"
                  dominantBaseline="central"
                >
                  {d.label}
                </text>
              );
            })}
          </svg>
        </div>

        {/* Dimension Breakdown table */}
        <div className="w-full md:flex-1 space-y-2">
          {dimensions.map((dim) => {
            const isLagging = dim.studentScore < dim.benchmarkScore * 0.7;
            return (
              <div
                key={dim.label}
                className="flex items-center justify-between p-2 rounded-lg bg-slate-950/50 border border-slate-800/80 text-xs"
              >
                <div className="flex items-center gap-2">
                  <span
                    className={`w-2 h-2 rounded-full ${
                      isLagging ? 'bg-rose-400' : 'bg-emerald-400'
                    }`}
                  />
                  <span className="text-slate-300 font-medium">{dim.label}</span>
                </div>
                <div className="flex items-center gap-3 font-mono">
                  <span className={isLagging ? 'text-rose-400 font-semibold' : 'text-emerald-400'}>
                    {dim.rawStudent}
                  </span>
                  <span className="text-slate-500">/</span>
                  <span className="text-slate-400">{dim.rawBenchmark}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

function indexToAngle(i: number): number {
  return i;
}
