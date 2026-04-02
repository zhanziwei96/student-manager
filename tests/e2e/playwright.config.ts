import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './',
  testMatch: ['**/*.spec.ts', '**/*.setup.ts'],
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : 3,
  reporter: 'html',
  timeout: 60000,
  use: {
    baseURL: 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 10000,
    navigationTimeout: 30000,
  },
  projects: [
    { name: 'setup', testMatch: /.*\.setup\.ts/, },
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        storageState: '.auth/admin.json',
      },
      dependencies: ['setup'],
    },
    {
      name: 'chromium-teacher',
      use: {
        ...devices['Desktop Chrome'],
        storageState: '.auth/teacher.json',
      },
      testMatch: ['teacher*.spec.ts'],
      dependencies: ['setup'],
    },
    {
      name: 'chromium-student',
      use: {
        ...devices['Desktop Chrome'],
        storageState: '.auth/student.json',
      },
      testMatch: ['student*.spec.ts'],
      dependencies: ['setup'],
    },
  ],
  webServer: {
    command: 'cd ../../frontend-v3 && pnpm dev',
    url: 'http://localhost:5173',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
