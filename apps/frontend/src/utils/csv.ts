import { PredictionHistoryItem } from '@shared/types';

export function exportHistoryToCsvFile(history: PredictionHistoryItem[]): void {
  if (history.length === 0) return;

  const headers = [
    'Thoi_Gian',
    'Ngay',
    'Hoc_Phan',
    'Nhom_Tuoi',
    'Tin_Chi',
    'Luot_Click',
    'Ket_Qua',
    'Xac_Suat_Rui_Ro',
  ];

  const rows = history.map((item) => [
    `"${item.time}"`,
    `"${item.date}"`,
    `"${item.module}"`,
    `"${item.age}"`,
    item.credits,
    item.clicks,
    item.prediction === 1 ? '"Nguy co cao"' : '"An toan"',
    `"${(item.confidence * 100).toFixed(1)}%"`,
  ]);

  const csvContent = '\uFEFF' + [headers.join(','), ...rows.map((r) => r.join(','))].join('\r\n');
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  anchor.download = `edurisk_history_${Date.now()}.csv`;
  anchor.click();
  URL.revokeObjectURL(url);
}
