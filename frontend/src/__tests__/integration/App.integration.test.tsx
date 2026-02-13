import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { AxiosResponse } from 'axios';
import axios from 'axios';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import App from '../../App';
import type { TemplateAnalysisResult } from '../../types';

// Mock axios
vi.mock('axios');

// Mock URL.createObjectURL
window.URL.createObjectURL = vi.fn(() => 'mock-url');

describe('App Integration', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  // ... (skipping first test which is already fixed mostly, I should target specific lines)
  // wait, replace_file_content replaces a block. I should be careful not to overwrite my previous fix if I target the whole file.
  // I will target specific blocks.

  it('completes the full flow: upload -> content input -> generate', async () => {
    const user = userEvent.setup();
    const { container } = render(<App />);

    // 1. Check initial state - wait for lazy-loaded components
    expect(screen.getByText(/AI PowerPoint Agent/i)).toBeInTheDocument();

    await waitFor(() => {
      expect(screen.getByText(/1. Upload PowerPoint Template/i)).toBeInTheDocument();
    });

    // Content source section should not be visible yet
    expect(screen.queryByText(/2. Choose Content Source/i)).not.toBeInTheDocument();

    // 2. Upload Template
    const file = new File(['(content)'], 'template.pptx', {
      type: 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    });

    const fileInputRetry = container.querySelector('input[type="file"]');
    expect(fileInputRetry).toBeInTheDocument();

    // Mock API response for analyze
    const analyzeResponse: Partial<AxiosResponse<TemplateAnalysisResult>> = {
      data: {
        filename: 'template.pptx',
        masters: [{ layouts: [{}, {}] }],
      } as TemplateAnalysisResult,
    };
    vi.mocked(axios.post).mockResolvedValueOnce(analyzeResponse);

    if (fileInputRetry) {
      await user.upload(fileInputRetry as HTMLElement, file);
    }

    // Wait for analysis to complete and Content Source section to appear
    await waitFor(() => {
      expect(screen.getByText(/Template Loaded: template.pptx/i)).toBeInTheDocument();
    });

    await waitFor(() => {
      expect(screen.getByText(/2. Choose Content Source/i)).toBeInTheDocument();
    });

    // 3. Select Markdown mode and enter content
    const markdownRadio = screen.getByLabelText(/Markdown Input/i);
    await user.click(markdownRadio);

    // Mock parseMarkdown API response
    const parseMarkdownResponse = {
      data: {
        presentation_title: 'Test Presentation',
        slides: [
          {
            layout_index: 0,
            title: 'Intro to AI',
            bullet_points: ['Point 1', 'Point 2'],
          },
        ],
        warnings: [],
      },
    };

    // Mock for parseMarkdown (via axios.post) - for both typing (live preview) and generation
    vi.mocked(axios.post).mockResolvedValue(parseMarkdownResponse as AxiosResponse);

    // Enter markdown content
    const markdownTextarea = screen.getByTestId('markdown-textarea');
    await user.type(markdownTextarea, '# Test\\n\\n## Intro to AI\\n- Point 1\\n- Point 2');

    // Click Generate from Markdown
    const generateBtn = screen.getByRole('button', {
      name: /Generate from Markdown/i,
    });

    await user.click(generateBtn);

    // Wait for Preview to appear
    await waitFor(() => {
      expect(screen.getByText(/3. Preview & Generate/i)).toBeInTheDocument();
    });

    expect(screen.getByText(/Slide 1: Intro to AI/i)).toBeInTheDocument();

    // 4. Generate Presentation
    const generatePptxBtn = screen.getByRole('button', {
      name: /Generate Presentation/i,
    });

    // Mock API response for generate
    const generateResponse: Partial<AxiosResponse<Blob>> = {
      data: new Blob(['mock content']),
    };
    vi.mocked(axios.post).mockResolvedValueOnce(generateResponse);

    await user.click(generatePptxBtn);

    // Wait for Download button
    await waitFor(() => {
      expect(screen.getByText(/Download .pptx/i)).toBeInTheDocument();
    });

    const downloadLink = screen.getByText(/Download .pptx/i);
    expect(downloadLink).toHaveAttribute('href', 'mock-url');
  });

  it('handles extraction flow', async () => {
    const user = userEvent.setup();
    const { container } = render(<App />);

    // Wait for upload button
    await waitFor(() => {
      expect(screen.getByText(/1. Upload PowerPoint Template/i)).toBeInTheDocument();
    });

    // Switch to Extraction Mode
    const extractModeRadio = screen.getByLabelText(/Extract Content/i);
    await user.click(extractModeRadio);

    // Upload Content File
    const file = new File(['(content)'], 'source.pptx', {
      type: 'application/vnd.openxmlformats-officedocument.presentationml.presentation',
    });
    const fileInput = container.querySelector('input[type="file"]');

    // Mock extract content response
    const extractResponse = {
      data: {
        filename: 'source.pptx',
        extraction_id: 'test-extraction-id',
        slides: [
          {
            title: 'Extracted Slide',
            bullet_points: [{ text: 'Extracted Point', level: 0 }],
            content_text: 'Extracted Content',
            image_refs: [],
          },
        ],
        images: [],
        charts: [],
        warnings: [],
      },
    };
    vi.mocked(axios.post).mockResolvedValueOnce(extractResponse as AxiosResponse);

    if (fileInput) {
      await user.upload(fileInput as HTMLElement, file);
    }

    // Wait for ContentInput to detect extracted content
    await waitFor(() => {
      expect(screen.getByTestId('source-extracted')).toBeInTheDocument();
    });

    // Select Extracted Content source
    const extractedSourceRadio = screen.getByTestId('source-extracted');
    await user.click(extractedSourceRadio);

    // Verify extraction usage prompt
    await waitFor(() => {
      expect(screen.getByText(/Using 1 slides from extracted PPTX content/i)).toBeInTheDocument();
    });

    // Click Use Extracted Content
    const useContentBtn = screen.getByRole('button', {
      name: /Use Extracted Content/i,
    });
    await user.click(useContentBtn);

    // Verify Preview
    await waitFor(() => {
      expect(screen.getByText(/3. Preview & Generate/i)).toBeInTheDocument();
    });
    expect(screen.getByText(/Slide 1: Extracted Slide/i)).toBeInTheDocument();
  });

  it('displays error when analysis fails', async () => {
    const user = userEvent.setup();
    const { container } = render(<App />);

    await waitFor(() => {
      expect(container.querySelector('input[type="file"]')).toBeInTheDocument();
    });

    const fileInput = container.querySelector('input[type="file"]');
    const file = new File([''], 'bad.pptx', { type: 'application/pdf' });

    vi.mocked(axios.post).mockRejectedValueOnce(new Error('Network Error'));

    if (fileInput) {
      await user.upload(fileInput as HTMLElement, file);
    }

    await waitFor(() => {
      expect(
        screen.getByText(/Failed to analyze template. Please try again./i)
      ).toBeInTheDocument();
    });
  });
});
