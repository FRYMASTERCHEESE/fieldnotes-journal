const { defineConfig } = require('@playwright/test');
module.exports = defineConfig({
  testDir: './browser-tests',
  timeout: 60000,
  workers: 3,
  retries: 0,
  webServer: process.env.SITE_URL?.startsWith('http://127.0.0.1:8000/') ? {
    command: 'python scripts/serve.py', url: process.env.SITE_URL, reuseExistingServer: !process.env.CI
  } : undefined,
  reporter: [['list'], ['json', { outputFile: 'test-results/results.json' }]],
  use: { baseURL: process.env.SITE_URL || 'https://frymastercheese.github.io/fieldnotes-journal/', screenshot: 'only-on-failure', trace: 'retain-on-failure' },
  projects: ['chromium', 'firefox', 'webkit'].map(browserName => ({ name: browserName, use: { browserName } }))
});
