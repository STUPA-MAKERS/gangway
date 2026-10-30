module.exports = {
  preset: 'jest-preset-angular',
  setupFilesAfterEnv: ['<rootDir>/setup-jest.ts'],
  testEnvironment: 'jsdom',
  roots: ['<rootDir>/src'],
  testMatch: ['**/*.spec.ts'],
  moduleNameMapper: {
    '^@stupa-makers/ui-kit$': '<rootDir>/vendor/ui-kit/src/public-api.ts',
    '^@stupa-makers/ui-kit/shell$': '<rootDir>/vendor/ui-kit/shell/src/public-api.ts',
    '^@stupa-makers/ui-kit/pwa$': '<rootDir>/vendor/ui-kit/pwa/src/public-api.ts',
    '\\.(css|scss)$': '<rootDir>/src/testing/style-mock.js',
  },
  transform: {
    '^.+\\.(ts|mjs|js|html)$': [
      'jest-preset-angular',
      {
        tsconfig: '<rootDir>/tsconfig.spec.json',
        stringifyContentPathRegex: '\\.(html|svg)$',
      },
    ],
  },
  transformIgnorePatterns: ['node_modules/(?!.*\\.mjs$|@angular|rxjs)'],
};
