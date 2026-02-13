import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import type { AxiosResponse } from 'axios';
import axios, { AxiosError } from 'axios';
import { describe, expect, it, vi } from 'vitest';
import { TopicInput } from '../TopicInput';

vi.mock('axios', async (importOriginal) => {
  const actual = await importOriginal<typeof import('axios')>();
  return {
    ...actual,
    default: {
      ...actual.default,
      post: vi.fn(),
      isAxiosError: actual.default.isAxiosError,
    },
  };
});

// Helper function to create AxiosError with response
function createAxiosError(status: number, data?: { detail?: string }): AxiosError {
  const error = new AxiosError(`Request failed with status ${status}`);
  error.response = {
    status,
    statusText: 'Error',
    data: data || {},
    headers: {},
    config: { headers: {} },
  } as AxiosError['response'];
  return error;
}

describe('TopicInput', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });
  it('renders and updates input value', async () => {
    render(<TopicInput onContentGenerated={() => {}} />);

    const input = screen.getByPlaceholderText(/e.g., The Future of AI/i);
    await userEvent.type(input, 'Test Topic');

    expect(input).toHaveValue('Test Topic');
  });

  it('calls API and returns content on button click', async () => {
    const handleGenerated = vi.fn();
    const mockSlides = [{ title: 'Slide 1', bullet_points: [], layout_index: 0 }];
    // Add delay to check loading state
    vi.mocked(axios.post).mockImplementation(
      () =>
        new Promise((resolve) =>
          setTimeout(() => resolve({ data: mockSlides }), 100)
        ) as unknown as Promise<AxiosResponse>
    );

    render(<TopicInput onContentGenerated={handleGenerated} />);

    const input = screen.getByPlaceholderText(/e.g., The Future of AI/i);
    await userEvent.type(input, 'Test Topic');

    const button = screen.getByRole('button', { name: /Generate Content/i });
    await userEvent.click(button);

    expect(button).toBeDisabled();
    expect(button).toHaveTextContent('Researching...');

    await waitFor(() => {
      expect(axios.post).toHaveBeenCalledWith('/api/research', null, {
        params: { topic: 'Test Topic' },
        timeout: 180000,
      });
      expect(handleGenerated).toHaveBeenCalledWith(mockSlides);
    });

    expect(button).toBeEnabled();
    expect(button).toHaveTextContent('Generate Content');
  });

  it('shows error on failure', async () => {
    vi.mocked(axios.post).mockRejectedValueOnce(new Error('Failed'));
    render(<TopicInput onContentGenerated={() => {}} />);

    const input = screen.getByPlaceholderText(/e.g., The Future of AI/i);
    await userEvent.type(input, 'Test Topic');

    const button = screen.getByRole('button', { name: /Generate Content/i });
    await userEvent.click(button);

    await waitFor(() => {
      // Updated to match the new English error message format
      expect(screen.getByText(/An unexpected error occurred/i)).toBeInTheDocument();
    });
  });

  it('shows timeout error message for ECONNABORTED', async () => {
    const axiosError = new AxiosError('timeout', 'ECONNABORTED');
    vi.mocked(axios.post).mockRejectedValueOnce(axiosError);

    render(<TopicInput onContentGenerated={() => {}} />);

    const input = screen.getByPlaceholderText(/e.g., The Future of AI/i);
    await userEvent.type(input, 'Test Topic');

    const button = screen.getByRole('button', { name: /Generate Content/i });
    await userEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText(/Request timed out/i)).toBeInTheDocument();
    });
  });

  it('shows network error message for ERR_NETWORK', async () => {
    const axiosError = new AxiosError('network error', 'ERR_NETWORK');
    vi.mocked(axios.post).mockRejectedValueOnce(axiosError);

    render(<TopicInput onContentGenerated={() => {}} />);

    const input = screen.getByPlaceholderText(/e.g., The Future of AI/i);
    await userEvent.type(input, 'Test Topic');

    const button = screen.getByRole('button', { name: /Generate Content/i });
    await userEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText(/Network error occurred/i)).toBeInTheDocument();
    });
  });

  it('shows validation error for 400 status', async () => {
    const axiosError = createAxiosError(400, { detail: 'Invalid topic' });
    vi.mocked(axios.post).mockRejectedValueOnce(axiosError);

    render(<TopicInput onContentGenerated={() => {}} />);

    const input = screen.getByPlaceholderText(/e.g., The Future of AI/i);
    await userEvent.type(input, 'Test Topic');

    const button = screen.getByRole('button', { name: /Generate Content/i });
    await userEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText(/Invalid input/i)).toBeInTheDocument();
    });
  });

  it('shows not found error for 404 status', async () => {
    const axiosError = createAxiosError(404);
    vi.mocked(axios.post).mockRejectedValueOnce(axiosError);

    render(<TopicInput onContentGenerated={() => {}} />);

    const input = screen.getByPlaceholderText(/e.g., The Future of AI/i);
    await userEvent.type(input, 'Test Topic');

    const button = screen.getByRole('button', { name: /Generate Content/i });
    await userEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText(/API endpoint not found/i)).toBeInTheDocument();
    });
  });

  it('shows server error for 500 status', async () => {
    const axiosError = createAxiosError(500, { detail: 'Database error' });
    vi.mocked(axios.post).mockRejectedValueOnce(axiosError);

    render(<TopicInput onContentGenerated={() => {}} />);

    const input = screen.getByPlaceholderText(/e.g., The Future of AI/i);
    await userEvent.type(input, 'Test Topic');

    const button = screen.getByRole('button', { name: /Generate Content/i });
    await userEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText(/Server error occurred/i)).toBeInTheDocument();
    });
  });

  it('shows service unavailable for 503 status', async () => {
    const axiosError = createAxiosError(503);
    vi.mocked(axios.post).mockRejectedValueOnce(axiosError);

    render(<TopicInput onContentGenerated={() => {}} />);

    const input = screen.getByPlaceholderText(/e.g., The Future of AI/i);
    await userEvent.type(input, 'Test Topic');

    const button = screen.getByRole('button', { name: /Generate Content/i });
    await userEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText(/Service temporarily unavailable/i)).toBeInTheDocument();
    });
  });

  it('shows generic error for other status codes', async () => {
    const axiosError = createAxiosError(429, { detail: 'Rate limited' });
    vi.mocked(axios.post).mockRejectedValueOnce(axiosError);

    render(<TopicInput onContentGenerated={() => {}} />);

    const input = screen.getByPlaceholderText(/e.g., The Future of AI/i);
    await userEvent.type(input, 'Test Topic');

    const button = screen.getByRole('button', { name: /Generate Content/i });
    await userEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText(/Error \(429\)/i)).toBeInTheDocument();
    });
  });

  it('shows connection failed error when axios error has no response', async () => {
    const axiosError = new AxiosError('Connection refused');
    axiosError.response = undefined;
    vi.mocked(axios.post).mockRejectedValueOnce(axiosError);

    render(<TopicInput onContentGenerated={() => {}} />);

    const input = screen.getByPlaceholderText(/e.g., The Future of AI/i);
    await userEvent.type(input, 'Test Topic');

    const button = screen.getByRole('button', { name: /Generate Content/i });
    await userEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText(/Failed to generate content/i)).toBeInTheDocument();
    });
  });

  it('does not call API when topic is empty', async () => {
    render(<TopicInput onContentGenerated={() => {}} />);

    const button = screen.getByRole('button', { name: /Generate Content/i });

    // Button should be disabled when topic is empty
    expect(button).toBeDisabled();

    // Clicking disabled button should not trigger API call
    await userEvent.click(button);

    expect(axios.post).not.toHaveBeenCalled();
  });

  it('shows validation error for 400 status without detail', async () => {
    const axiosError = createAxiosError(400); // No detail field
    vi.mocked(axios.post).mockRejectedValueOnce(axiosError);

    render(<TopicInput onContentGenerated={() => {}} />);

    const input = screen.getByPlaceholderText(/e.g., The Future of AI/i);
    await userEvent.type(input, 'Test Topic');

    const button = screen.getByRole('button', { name: /Generate Content/i });
    await userEvent.click(button);

    await waitFor(() => {
      // Should show fallback message when detail is missing
      expect(screen.getByText(/Invalid input/i)).toBeInTheDocument();
      expect(screen.getByText(/Please check your topic/i)).toBeInTheDocument();
    });
  });

  it('shows server error for 500 status without detail', async () => {
    const axiosError = createAxiosError(500); // No detail field
    vi.mocked(axios.post).mockRejectedValueOnce(axiosError);

    render(<TopicInput onContentGenerated={() => {}} />);

    const input = screen.getByPlaceholderText(/e.g., The Future of AI/i);
    await userEvent.type(input, 'Test Topic');

    const button = screen.getByRole('button', { name: /Generate Content/i });
    await userEvent.click(button);

    await waitFor(() => {
      // Should show fallback message when detail is missing
      expect(screen.getByText(/Server error occurred/i)).toBeInTheDocument();
      expect(screen.getByText(/Unexpected error/i)).toBeInTheDocument();
    });
  });

  it('shows generic error for unknown status without detail', async () => {
    const axiosError = createAxiosError(418); // Teapot status, no detail
    vi.mocked(axios.post).mockRejectedValueOnce(axiosError);

    render(<TopicInput onContentGenerated={() => {}} />);

    const input = screen.getByPlaceholderText(/e.g., The Future of AI/i);
    await userEvent.type(input, 'Test Topic');

    const button = screen.getByRole('button', { name: /Generate Content/i });
    await userEvent.click(button);

    await waitFor(() => {
      // Should show status code and fallback to error message
      expect(screen.getByText(/Error \(418\)/i)).toBeInTheDocument();
    });
  });

  it('clears error when new research starts', async () => {
    // First request fails
    vi.mocked(axios.post).mockRejectedValueOnce(new Error('First error'));

    render(<TopicInput onContentGenerated={() => {}} />);

    const input = screen.getByPlaceholderText(/e.g., The Future of AI/i);
    await userEvent.type(input, 'Test Topic');

    const button = screen.getByRole('button', { name: /Generate Content/i });
    await userEvent.click(button);

    await waitFor(() => {
      expect(screen.getByText(/An unexpected error occurred/i)).toBeInTheDocument();
    });

    // Second request succeeds
    vi.mocked(axios.post).mockResolvedValueOnce({
      data: [{ title: 'Success', bullet_points: [], layout_index: 0 }],
    } as AxiosResponse);

    await userEvent.click(button);

    // Error should be cleared
    await waitFor(() => {
      expect(screen.queryByText(/An unexpected error occurred/i)).not.toBeInTheDocument();
    });
  });

  it('handles non-Error object being thrown', async () => {
    // Throw a string instead of Error object to test line 77 branch
    vi.mocked(axios.post).mockRejectedValueOnce('String error');

    render(<TopicInput onContentGenerated={() => {}} />);

    const input = screen.getByPlaceholderText(/e.g., The Future of AI/i);
    await userEvent.type(input, 'Test Topic');

    const button = screen.getByRole('button', { name: /Generate Content/i });
    await userEvent.click(button);

    await waitFor(() => {
      // Should show "Unknown error" when thrown value is not an Error instance
      expect(screen.getByText(/Unknown error/i)).toBeInTheDocument();
    });
  });
});
