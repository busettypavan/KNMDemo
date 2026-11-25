// Jest for a React app: jsdom, TypeScript through ts-jest, Testing Library matchers and polyfills from src/testing/setup.ts,
// coverage gate on application code (scaffold glue excluded).
module.exports = {
  testEnvironment: 'jsdom',
  roots: ['<rootDir>/src', '<rootDir>/tests'],
  testMatch: ['**/*.test.ts', '**/*.test.tsx'],
  transform: { '^.+\\.tsx?$': 'ts-jest' },
  // tests import the untyped scripts/*.cjs helpers (TS7016)
  globals: { 'ts-jest': { diagnostics: { ignoreCodes: [7016] } } },
  // react-financial-charts is ESM and draws on a canvas: tests get a stub (tests that check its props mock it themselves)
  moduleNameMapper: { '^react-financial-charts$': '<rootDir>/tests/support/react-financial-charts.stub.ts' },
  // first import of the app shell compiles Chakra and the router through ts-jest: slow when suites run in parallel
  testTimeout: 30000,
  setupFilesAfterEnv: ['<rootDir>/src/testing/setup.ts'],
  collectCoverageFrom: ['src/**/*.{ts,tsx}', '!src/app/{providers,router,theme,config}.{ts,tsx}', '!src/main.tsx', '!**/*.d.ts'],
  coverageThreshold: { global: { statements: 80, lines: 80, functions: 80, branches: 70 } }
};
