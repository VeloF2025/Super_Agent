/**
 * Test Setup and Configuration
 * Global test utilities and environment setup
 */

import { jest } from '@jest/globals';
import path from 'path';
import { fileURLToPath } from 'url';
import { dirname } from 'path';
import fs from 'fs';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

// Set test environment
process.env.NODE_ENV = 'test';
process.env.JWT_SECRET = 'test-secret-key-for-testing-only';
process.env.DATABASE_URL = ':memory:';
process.env.PORT = '0'; // Use random port for tests

// Create test data directory
const testDataDir = path.join(__dirname, 'test-data');
if (!fs.existsSync(testDataDir)) {
  fs.mkdirSync(testDataDir, { recursive: true });
}

// Mock console methods to reduce test output noise
global.console = {
  ...console,
  log: jest.fn(),
  error: jest.fn(),
  warn: jest.fn(),
  info: jest.fn(),
  debug: jest.fn()
};

// Global test utilities
global.testUtils = {
  // Generate test JWT token
  generateTestToken(user = { userId: 'test-user', username: 'testuser', role: 'admin' }) {
    const jwt = require('jsonwebtoken');
    return jwt.sign(user, process.env.JWT_SECRET, { expiresIn: '1h' });
  },

  // Create test agent data
  createTestAgent(overrides = {}) {
    return {
      id: 'test-agent-1',
      name: 'Test Agent',
      type: 'development',
      status: 'online',
      capabilities: ['coding', 'testing'],
      location: '/test/location',
      project: 'test-project',
      ...overrides
    };
  },

  // Create test activity data
  createTestActivity(overrides = {}) {
    return {
      agent_id: 'test-agent-1',
      activity_type: 'test_activity',
      description: 'Test activity description',
      status: 'in_progress',
      priority: 'medium',
      ...overrides
    };
  },

  // Clean up test data after each test
  async cleanupTestData() {
    if (fs.existsSync(testDataDir)) {
      fs.rmSync(testDataDir, { recursive: true, force: true });
      fs.mkdirSync(testDataDir, { recursive: true });
    }
  }
};

// Clean up after each test
afterEach(async () => {
  await global.testUtils.cleanupTestData();
  jest.clearAllMocks();
});

// Clean up after all tests
afterAll(async () => {
  if (fs.existsSync(testDataDir)) {
    fs.rmSync(testDataDir, { recursive: true, force: true });
  }
});