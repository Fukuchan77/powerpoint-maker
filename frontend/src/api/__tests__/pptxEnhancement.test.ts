import axios from 'axios';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { extractContent, parseMarkdown } from '../pptxEnhancement';

vi.mock('axios');
const mockedAxios = vi.mocked(axios, true);

describe('pptxEnhancement API', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  describe('extractContent', () => {
    it('handles network errors gracefully', async () => {
      const file = new File(['content'], 'test.pptx');
      mockedAxios.post.mockRejectedValue(new Error('Network Error'));

      await expect(extractContent(file, 'content')).rejects.toThrow();
    });

    it('handles timeout errors', async () => {
      const file = new File(['content'], 'test.pptx');
      mockedAxios.post.mockRejectedValue({ code: 'ECONNABORTED' });

      await expect(extractContent(file, 'content')).rejects.toThrow();
    });

    it('handles 400 errors', async () => {
      const file = new File(['content'], 'test.pptx');
      mockedAxios.post.mockRejectedValue({
        response: { status: 400, data: { detail: 'Invalid file' } },
      });

      await expect(extractContent(file, 'content')).rejects.toThrow();
    });

    it('handles 500 errors', async () => {
      const file = new File(['content'], 'test.pptx');
      mockedAxios.post.mockRejectedValue({
        response: { status: 500, data: { detail: 'Server error' } },
      });

      await expect(extractContent(file, 'content')).rejects.toThrow();
    });
  });

  describe('parseMarkdown', () => {
    it('handles syntax errors with location info', async () => {
      mockedAxios.post.mockRejectedValue({
        response: {
          status: 400,
          data: {
            detail: {
              error_code: 'MARKDOWN_SYNTAX_ERROR',
              message: 'No slides found',
              location: { line: 1, column: 1 },
            },
          },
        },
      });

      await expect(parseMarkdown('invalid')).rejects.toThrow();
    });

    it('handles network timeouts', async () => {
      mockedAxios.post.mockRejectedValue({ code: 'ETIMEDOUT' });

      await expect(parseMarkdown('# Test')).rejects.toThrow();
    });
  });
});
