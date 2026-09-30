export function supportReport(result) {
  const prediction = result.prediction
  const lines = [
    '# Phiếu dự báo và gợi ý học tập', '',
    'Học phần/kỳ: ' + result.course,
    'Thời điểm: ngày ' + result.cutoff_day + ' — cutoff 75%.',
    'Phiên bản quy tắc: ' + result.rule_version, '',
    '## Dự báo nguy cơ',
    prediction ? 'Xác suất ước lượng: ' + (prediction.probability_risk * 100).toFixed(1) + '%. Ngưỡng demo: ' + (prediction.threshold * 100) + '%.' : 'Chưa chạy model vì chưa đủ xác nhận dữ liệu.',
    'Không phải điểm số, xác suất đã hiệu chỉnh hay quyết định học vụ.', '',
    '## Gợi ý và bằng chứng',
  ]
  for (const suggestion of result.suggestions) {
    lines.push('', '### ' + suggestion.rule_id + ' — ' + suggestion.title,
      suggestion.observation, '', 'Hành động: ' + suggestion.action,
      ...suggestion.evidence.map((item) => '- ' + item),
      'Giới hạn: ' + suggestion.limitation)
  }
  if (!result.suggestions.length) lines.push('Chưa đủ căn cứ để đưa ra gợi ý cụ thể trong bốn tình huống.')
  lines.push('', '## Giới hạn và nguồn dữ liệu', ...result.warnings.map((item) => '- ' + item), result.notice)
  if (result.source_notice) lines.push(result.source_notice)
  return lines.join('\n') + '\n'
}
