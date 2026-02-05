// tests/process-fixtures.test.ts
import { describe, it, expect } from 'vitest';
import { listFixtures, loadFixture } from './fixture-loader.js';
import { processContent } from '../src/index.js';

describe('fixture processing', () => {
  it('processes all valid fixtures without errors', async () => {
    const fixtures = await listFixtures();
    const validFixtures = fixtures.filter(f => f.startsWith('valid/'));

    for (const fixtureName of validFixtures) {
      const fixture = await loadFixture(fixtureName);
      const result = processContent(fixture.input);

      expect(result.errors, `Fixture ${fixtureName} should have no errors`).toEqual([]);
    }
  });

  it('matches expected output for each valid fixture', async () => {
    const fixtures = await listFixtures();
    const validFixtures = fixtures.filter(f => f.startsWith('valid/'));

    for (const fixtureName of validFixtures) {
      const fixture = await loadFixture(fixtureName);
      const result = processContent(fixture.input);

      expect(result, `Fixture ${fixtureName}`).toEqual(fixture.expected);
    }
  });

  it('produces expected errors for invalid fixtures', async () => {
    const fixtures = await listFixtures();
    const invalidFixtures = fixtures.filter(f => f.startsWith('invalid/'));

    for (const fixtureName of invalidFixtures) {
      const fixture = await loadFixture(fixtureName);
      const result = processContent(fixture.input);

      expect(result.errors.length, `Fixture ${fixtureName} should have errors`).toBeGreaterThan(0);
      expect(result.errors, `Fixture ${fixtureName}`).toEqual(fixture.expected.errors);
    }
  });
});
