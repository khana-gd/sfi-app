import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: false, // Run sequentially to avoid DB lock conflicts
  timeout: 30000,
  forbidOnly: !!process.env.CI,
  retries: 0,
  workers: 1,
  reporter: 'list',
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: [
    {
      command: 'npm run dev',
      cwd: './frontend',
      url: 'http://localhost:5173',
      reuseExistingServer: true,
    },
    {
      command: '.venv\\Scripts\\uvicorn app.main:app --port 8000',
      cwd: './backend',
      url: 'http://localhost:8000/api/v1/health',
      reuseExistingServer: true,
    }
  ]
});
