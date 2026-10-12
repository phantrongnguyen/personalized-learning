import React, { useEffect, useId, useRef, useState } from 'react';
import { StudentFeatures } from '@shared/types';
import { BENCHMARKS } from '@shared/constants';

interface RadarProps {
  features: StudentFeatures;
}

interface Dimension {
  label: string;
  axisLabel: string[];
  studentScore: number; // 0 to 1
  benchmarkScore: number; // 0 to 1
  rawStudent: string;
  rawBenchmark: string;
}

export const RadarCompetencyChart: React.FC<RadarProps> = ({ features }) => {
  const [activeDimension, setActiveDimension] = useState<number | null>(null);
  const chartRef = useRef<HTMLDivElement>(null);
  const tooltipId = useId();

  useEffect(() => {
    if (activeDimension === null) return;

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') setActiveDimension(null);
    };
    const handlePointerDown = (event: PointerEvent) => {
      if (event.target instanceof Node && !chartRef.current?.contains(event.target)) {
        setActiveDimension(null);
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    document.addEventListener('pointerdown', handlePointerDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
      document.removeEventListener('pointerdown', handlePointerDown);
    };
  }, [activeDimension]);

  // Normalize each metric to 0..1 scale
  const dimensions: Dimension[] = [
    {
      label: 'Độ chuyên cần',
      axisLabel: ['Chuyên cần'],
      studentScore: Math.min(1, Math.max(0, features.active_days_to_t / 100)),
      benchmarkScore: Math.min(1, BENCHMARKS.active_days_to_t / 100),
      rawStudent: `${features.active_days_to_t} ngày`,
      rawBenchmark: `${BENCHMARKS.active_days_to_t} ngày`,
    },
    {
      label: 'Tổng lượt tương tác',
      axisLabel: ['Tổng lượt', 'tương tác'],
      studentScore: Math.min(1, Math.max(0, features.total_clicks_to_t / 3000)),
      benchmarkScore: Math.min(1, BENCHMARKS.total_clicks_to_t / 3000),
      rawStudent: `${features.total_clicks_to_t} clicks`,
      rawBenchmark: `${BENCHMARKS.total_clicks_to_t} clicks`,
    },
    {
      label: 'Tương tác 7 ngày gần nhất',
      axisLabel: ['Tương tác', '7 ngày'],
      studentScore: Math.min(1, Math.max(0, features.clicks_recent_7 / 150)),
      benchmarkScore: Math.min(1, BENCHMARKS.clicks_recent_7 / 150),
      rawStudent: `${features.clicks_recent_7} clicks`,
      rawBenchmark: `${BENCHMARKS.clicks_recent_7} clicks`,
    },
    {
      label: 'Tỷ lệ nộp bài',
      axisLabel: ['Nộp bài'],
      studentScore: Math.min(1, Math.max(0, features.submission_rate)),
      benchmarkScore: BENCHMARKS.submission_rate,
      rawStudent: `${(features.submission_rate * 100).toFixed(0)}%`,
      rawBenchmark: `${(BENCHMARKS.submission_rate * 100).toFixed(0)}%`,
    },
    {
      label: 'Kỷ luật đúng hạn',
      axisLabel: ['Đúng hạn'],
      studentScore: Math.max(0, 1 - features.late_submissions_to_t * 0.3),
      benchmarkScore: 0.95,
      rawStudent: `${features.late_submissions_to_t} trễ`,
      rawBenchmark: `≤ 0 bài`,
    },
    {
      label: 'Tỷ lệ ngày học',
      axisLabel: ['Tỷ lệ', 'ngày học'],
      studentScore: Math.min(1, Math.max(0, features.active_day_ratio)),
      benchmarkScore: BENCHMARKS.active_day_ratio,
      rawStudent: `${(features.active_day_ratio * 100).toFixed(0)}%`,
      rawBenchmark: `${(BENCHMARKS.active_day_ratio * 100).toFixed(0)}%`,
    },
  ];

  const totalPoints = dimensions.length;
  const width = 360;
  const height = 320;
  const centerX = width / 2;
  const centerY = height / 2;
  const maxRadius = 104;

  // Calculate polygon points
  const getCoordinates = (value: number, index: number): [number, number] => {
    const angle = (Math.PI * 2 / totalPoints) * index - Math.PI / 2;
    const r = value * maxRadius;
    const x = centerX + r * Math.cos(angle);
    const y = centerY + r * Math.sin(angle);
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
  const activeMetric = activeDimension === null ? null : dimensions[activeDimension];

  return (
    <section aria-label="Đối sánh Năng lực & Hành vi" className="competency-card min-w-0 bg-slate-900/90 rounded-2xl border border-slate-800 shadow-xl p-4 sm:p-6">
      <div className="flex flex-wrap items-start justify-between gap-4 mb-6">
        <div className="min-w-0 flex-1 basis-64">
          <h3 className="text-base font-bold text-foreground">Đối sánh Năng lực & Hành vi</h3>
          <p className="text-xs text-slate-400">So sánh với ngưỡng trung vị sinh viên Giỏi (OULAD)</p>
        </div>

        {/* Legend */}
        <div className="flex flex-wrap items-center gap-x-4 gap-y-2 text-xs font-medium">
          <div className="flex items-center gap-1.5 text-emerald-400">
            <span className="w-3 h-3 shrink-0 rounded-full bg-emerald-500/30 border border-emerald-400" />
            <span>Sinh viên hiện tại</span>
          </div>
          <div className="flex items-center gap-1.5 text-blue-400">
            <span className="w-3 h-3 shrink-0 rounded-full bg-blue-500/20 border border-blue-400 border-dashed" />
            <span>Chuẩn Benchmark</span>
          </div>
        </div>
      </div>

      <div className="competency-layout">
        {/* SVG Radar */}
        <div
          ref={chartRef}
          className="w-full min-w-0 max-w-[360px] mx-auto"
          onPointerLeave={(event) => {
            if (event.pointerType === 'mouse' && !event.currentTarget.contains(document.activeElement)) {
              setActiveDimension(null);
            }
          }}
          onBlur={(event) => {
            if (!event.currentTarget.contains(event.relatedTarget)) setActiveDimension(null);
          }}
        >
          <svg viewBox={`0 0 ${width} ${height}`} role="group" aria-label="Biểu đồ radar tương tác. Rê chuột, chạm hoặc dùng Tab để xem từng chỉ số; nhấn Escape để ẩn." className="block w-full h-auto">
            <title>Đối sánh sáu chỉ số hành vi học tập</title>
            <desc>Đường liền màu xanh lá là sinh viên hiện tại; đường nét đứt màu xanh dương là chuẩn đối sánh. Các trục đánh số từ 1 đến 6 tương ứng với danh sách chi tiết.</desc>
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
                  stroke="rgb(var(--color-slate-800))"
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
                  x1={centerX}
                  y1={centerY}
                  x2={x}
                  y2={y}
                  stroke="rgb(var(--color-slate-700))"
                  strokeWidth="1"
                />
              );
            })}

            {/* Benchmark polygon */}
            <polygon
              points={benchmarkPolygon}
              fill="rgb(var(--color-chart-benchmark) / 0.15)"
              stroke="rgb(var(--color-chart-benchmark))"
              strokeWidth="2"
              strokeDasharray="4,3"
            />

            {/* Student polygon */}
            <polygon
              points={studentPolygon}
              fill="rgb(var(--color-chart-student) / 0.25)"
              stroke="rgb(var(--color-chart-student))"
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
                  fill="rgb(var(--color-chart-student))"
                  stroke="rgb(var(--color-slate-900))"
                  strokeWidth="1.5"
                />
              );
            })}

            {/* Dimension Labels */}
            {dimensions.map((d, i) => {
              const angle = (Math.PI * 2 / totalPoints) * i - Math.PI / 2;
              const labelRadius = maxRadius + 23;
              const lx = centerX + labelRadius * Math.cos(angle);
              const ly = centerY + labelRadius * Math.sin(angle);

              let textAnchor: 'middle' | 'start' | 'end' = 'middle';
              if (Math.cos(angle) > 0.3) textAnchor = 'start';
              else if (Math.cos(angle) < -0.3) textAnchor = 'end';

              return (
                <g key={d.label} aria-hidden="true">
                  <text x={lx} y={ly} textAnchor={textAnchor} fontSize="12" className="competency-axis-label fill-slate-300 font-semibold">
                    {d.axisLabel.map((line, lineIndex) => (
                      <tspan key={line} x={lx} dy={lineIndex === 0 ? `${-((d.axisLabel.length - 1) * 7)}px` : '14px'} dominantBaseline="central">{line}</tspan>
                    ))}
                  </text>
                  <g className="competency-axis-number">
                    <circle cx={lx} cy={ly} r="14" fill="rgb(var(--color-slate-900))" stroke="rgb(var(--color-slate-600))" />
                    <text x={lx} y={ly} textAnchor="middle" dominantBaseline="central" fontSize="18" className="fill-slate-200 font-semibold">{i + 1}</text>
                  </g>
                </g>
              );
            })}
            {dimensions.map((dimension, index) => {
              const angle = (Math.PI * 2 / totalPoints) * index - Math.PI / 2;
              const hitRadius = 145;
              const halfAngle = Math.PI / totalPoints;
              const startX = centerX + hitRadius * Math.cos(angle - halfAngle);
              const startY = centerY + hitRadius * Math.sin(angle - halfAngle);
              const endX = centerX + hitRadius * Math.cos(angle + halfAngle);
              const endY = centerY + hitRadius * Math.sin(angle + halfAngle);
              const [studentX, studentY] = getCoordinates(dimension.studentScore, index);
              const [benchmarkX, benchmarkY] = getCoordinates(dimension.benchmarkScore, index);
              const isActive = activeDimension === index;

              return (
                <g
                  key={dimension.label}
                  role="button"
                  tabIndex={0}
                  aria-label={`${dimension.label}: hiện tại ${dimension.rawStudent}, chuẩn đối sánh ${dimension.rawBenchmark}`}
                  aria-describedby={isActive ? tooltipId : undefined}
                  className="competency-hit cursor-pointer"
                  onPointerEnter={(event) => {
                    if (event.pointerType === 'mouse') setActiveDimension(index);
                  }}
                  onFocus={() => setActiveDimension(index)}
                  onClick={() => setActiveDimension(index)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter' || event.key === ' ') {
                      event.preventDefault();
                      setActiveDimension(index);
                    }
                  }}
                >
                  <path
                    d={`M ${centerX} ${centerY} L ${startX} ${startY} A ${hitRadius} ${hitRadius} 0 0 1 ${endX} ${endY} Z`}
                    fill={isActive ? 'rgb(var(--color-chart-benchmark) / 0.08)' : 'transparent'}
                    className="competency-sector"
                  />
                  {isActive && (
                    <g pointerEvents="none" aria-hidden="true">
                      <circle cx={studentX} cy={studentY} r="7" fill="rgb(var(--color-chart-student))" stroke="#f8fafc" strokeWidth="2" />
                      <circle cx={benchmarkX} cy={benchmarkY} r="5" fill="rgb(var(--color-slate-900))" stroke="rgb(var(--color-chart-benchmark))" strokeWidth="2" strokeDasharray="2,2" />
                    </g>
                  )}
                </g>
              );
            })}
          </svg>
          <p className="competency-axis-hint mt-2 text-center text-xs leading-relaxed text-slate-400">Trục 1–6 tương ứng với các chỉ số bên dưới.</p>
          <div className="competency-tooltip-slot mt-4">
            {activeMetric ? (
              <div id={tooltipId} role="tooltip" className="min-w-0 rounded-xl border border-blue-400/40 bg-slate-950/90 p-3 text-xs leading-relaxed">
                <p className="font-semibold text-foreground">{activeMetric.label}</p>
                <dl className="mt-2 grid grid-cols-2 gap-3">
                  <div className="min-w-0">
                    <dt className="text-slate-400">Sinh viên hiện tại</dt>
                    <dd className="mt-1 font-mono text-emerald-300 [overflow-wrap:anywhere]">{activeMetric.rawStudent}</dd>
                  </div>
                  <div className="min-w-0">
                    <dt className="text-slate-400">Chuẩn đối sánh</dt>
                    <dd className="mt-1 font-mono text-blue-300 [overflow-wrap:anywhere]">{activeMetric.rawBenchmark}</dd>
                  </div>
                </dl>
                <p className="mt-2 text-[11px] text-slate-400">Giá trị thực; vị trí trên radar được chuẩn hóa, không phải xác suất rủi ro.</p>
              </div>
            ) : (
              <p className="rounded-xl border border-dashed border-slate-700 p-3 text-xs leading-relaxed text-slate-400">Rê chuột lên vùng trục để xem chỉ số. Trên điện thoại, chạm vào biểu đồ; bàn phím dùng Tab. Nhấn Esc hoặc chạm bên ngoài để ẩn.</p>
            )}
          </div>
        </div>

        {/* Dimension Breakdown table */}
        <dl className="competency-breakdown w-full min-w-0 space-y-2">
          {dimensions.map((dim, index) => {
            const isLagging = dim.studentScore < dim.benchmarkScore * 0.7;
            return (
              <div
                key={dim.label}
                className={`competency-row p-3 rounded-lg bg-slate-950/50 border border-slate-800/80 text-xs ${activeDimension === index ? 'ring-1 ring-blue-400/70' : ''}`}
              >
                <dt className="flex min-w-0 items-start gap-2 leading-relaxed">
                  <span className="competency-dimension-number flex h-5 w-5 shrink-0 items-center justify-center rounded-full border border-slate-600 text-[11px] text-slate-300">{index + 1}</span>
                  <span
                    aria-hidden="true"
                    className={`mt-1 w-2 h-2 shrink-0 rounded-full ${
                      isLagging ? 'bg-rose-400' : 'bg-emerald-400'
                    }`}
                  />
                  <span className="min-w-0 break-words text-slate-300 font-medium">{dim.label}</span>
                </dt>
                <dd className="grid min-w-0 grid-cols-2 gap-3 leading-relaxed">
                  <div className="min-w-0">
                    <span className="block text-[10px] text-slate-500">Hiện tại</span>
                    <span className={`block font-mono [overflow-wrap:anywhere] ${isLagging ? 'text-rose-400 font-semibold' : 'text-emerald-400'}`}>{dim.rawStudent}</span>
                  </div>
                  <div className="min-w-0">
                    <span className="block text-[10px] text-slate-500">Chuẩn đối sánh</span>
                    <span className="block font-mono text-slate-400 [overflow-wrap:anywhere]">{dim.rawBenchmark}</span>
                  </div>
                </dd>
              </div>
            );
          })}
        </dl>
      </div>
    </section>
  );
};

