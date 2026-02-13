/**
 * API client functions for Layout Intelligence features
 */
import axios from 'axios';
import type { SlideContent } from '../types';

const API_BASE = '/api';

export interface LayoutIntelligenceRequest {
  text: string;
  template_id?: string;
}

export interface LayoutIntelligenceResponse {
  slides: SlideContent[];
  warnings: string[];
}

/**
 * Generate slides from raw text using AI-powered layout intelligence
 *
 * @param text - Raw text input (1-10000 characters)
 * @param templateId - Optional template ID for layout mapping
 * @returns Promise with generated slides and warnings
 */
export async function generateFromText(
  text: string,
  templateId?: string
): Promise<LayoutIntelligenceResponse> {
  const response = await axios.post<LayoutIntelligenceResponse>(
    `${API_BASE}/layout-intelligence`,
    {
      text,
      template_id: templateId,
    },
    {
      timeout: 65000, // 65 seconds (slightly longer than backend 60s timeout)
    }
  );
  return response.data;
}

// Made with Bob
