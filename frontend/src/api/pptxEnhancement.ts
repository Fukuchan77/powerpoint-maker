/**
 * API client functions for PPTX Enhancement features
 */
import axios from 'axios';
import type { AnalysisMode, ContentExtractionResult, MarkdownParseResponse } from '../types';

const API_BASE = '/api';

/**
 * Extract content from a PPTX file
 */
export async function extractContent(
  file: File,
  mode: AnalysisMode = 'content'
): Promise<ContentExtractionResult> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await axios.post<ContentExtractionResult>(
    `${API_BASE}/extract-content`,
    formData,
    {
      params: { mode },
      headers: { 'Content-Type': 'multipart/form-data' },
      timeout: 120000,
    }
  );
  return response.data;
}

/**
 * Parse Markdown content to slides
 */
export async function parseMarkdown(content: string): Promise<MarkdownParseResponse> {
  const response = await axios.post<MarkdownParseResponse>(
    `${API_BASE}/parse-markdown`,
    { content },
    { timeout: 30000 }
  );
  return response.data;
}
