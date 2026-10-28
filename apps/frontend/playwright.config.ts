import { defineConfig } from '@playwright/test';

if (process.env.EDURISK_E2E_RUN !== '1' || !/^e2e_[a-f0-9]{12}_test$/.test(process.env.E2E_DATABASE_NAME || '') ||
    !/^http:\/\/127\.0\.0\.1:\d+$/.test(process.env.E2E_BASE_URL || '')) {
  throw new Error('Use python scripts/run_browser_tests.py to provision an isolated environment');
}
export default defineConfig({
  testDir: './e2e', workers: 1, retries: 0, timeout: 120_000,
  expect: { timeout: 15_000 },
  outputDir: '../../reports/test-results/browser/artifacts',
  reporter: [['list'], ['json', { outputFile: '../../reports/test-results/browser/results.json' }],
    ['html', { outputFolder: '../../reports/test-results/browser/html', open: 'never' }]],
  use: { baseURL: process.env.E2E_BASE_URL, browserName: 'chromium', headless: true,
    actionTimeout: 15000, screenshot: 'only-on-failure', trace: 'retain-on-failure', viewport: { width: 1440, height: 1000 } },
});
