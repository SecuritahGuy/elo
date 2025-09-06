// Jest setup file for comprehensive testing
import '@testing-library/jest-dom';

// Mock Date properly to avoid breaking other libraries
const mockDate = new Date('2025-09-05T21:00:00Z');

// Store original Date
const OriginalDate = global.Date;

// Mock Date.now specifically for our tests
global.Date.now = jest.fn(() => mockDate.getTime());

// Create a proper Date mock that preserves all methods
class MockDate extends OriginalDate {
  constructor(...args) {
    if (args.length === 0) {
      super(mockDate.getTime());
    } else {
      super(...args);
    }
  }
}

// Copy all static methods from original Date
Object.setPrototypeOf(MockDate, OriginalDate);
Object.getOwnPropertyNames(OriginalDate).forEach(name => {
  if (name !== 'prototype' && name !== 'length' && name !== 'name') {
    MockDate[name] = OriginalDate[name];
  }
});

// Replace global Date with our mock
global.Date = MockDate;

// Mock console methods to avoid noise in tests
global.console = {
  ...console,
  log: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
};

// Mock IntersectionObserver
global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Mock ResizeObserver
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}));

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // deprecated
    removeListener: jest.fn(), // deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
});

// Mock window.location
Object.defineProperty(window, 'location', {
  value: {
    href: 'http://localhost:3000',
    origin: 'http://localhost:3000',
    pathname: '/',
    search: '',
    hash: '',
  },
  writable: true,
});

// Mock localStorage
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.localStorage = localStorageMock;

// Mock sessionStorage
const sessionStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
global.sessionStorage = sessionStorageMock;

// Suppress specific console warnings in tests
const originalError = console.error;
beforeAll(() => {
  console.error = (...args) => {
    if (
      typeof args[0] === 'string' &&
      args[0].includes('Warning: ReactDOM.render is no longer supported')
    ) {
      return;
    }
    originalError.call(console, ...args);
  };
});

afterAll(() => {
  console.error = originalError;
});