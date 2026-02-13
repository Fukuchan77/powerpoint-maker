import axios from 'axios';
import { useState } from 'react';
import type { SlideContent } from '../types';
import { createLogger } from '../utils/logger';

const logger = createLogger('TopicInput');

interface TopicInputProps {
  onContentGenerated: (slides: SlideContent[]) => void;
}

export function TopicInput({ onContentGenerated }: TopicInputProps) {
  const [topic, setTopic] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleResearch = async () => {
    if (!topic) return;
    setLoading(true);
    setError(null);

    try {
      console.log(`[TopicInput] Starting research for topic: "${topic}"`);
      const response = await axios.post('/api/research', null, {
        params: { topic }, // POST query param as per routes.py definition: async def research_topic(topic: str)
        timeout: 180000, // 3 minutes timeout for long-running research
      });
      console.log('[TopicInput] Research completed successfully');
      console.log('[TopicInput] Response data:', response.data);
      onContentGenerated(response.data);
    } catch (err) {
      logger.error('research_failed', err as Error, { topic });

      // Detailed error logging
      if (axios.isAxiosError(err)) {
        console.error('[TopicInput] Axios error details:', {
          message: err.message,
          code: err.code,
          status: err.response?.status,
          statusText: err.response?.statusText,
          data: err.response?.data,
        });

        // Enhanced error handling with specific status codes
        if (err.code === 'ECONNABORTED') {
          setError('Request timed out. Research is taking longer than expected. Please try again.');
        } else if (err.code === 'ERR_NETWORK') {
          setError('Network error occurred. Please check your internet connection.');
        } else if (err.response?.status === 400) {
          setError(`Invalid input: ${err.response?.data?.detail || 'Please check your topic'}`);
        } else if (err.response?.status === 404) {
          setError('API endpoint not found. Please check server configuration.');
        } else if (err.response?.status === 500) {
          setError(`Server error occurred: ${err.response?.data?.detail || 'Unexpected error'}`);
        } else if (err.response?.status === 503) {
          setError('Service temporarily unavailable. Please try again later.');
        } else if (err.response?.status) {
          setError(`Error (${err.response.status}): ${err.response?.data?.detail || err.message}`);
        } else {
          setError(`Failed to generate content: ${err.message}`);
        }
      } else {
        console.error('[TopicInput] Non-axios error:', err);
        const errorMessage = err instanceof Error ? err.message : 'Unknown error';
        setError(`An unexpected error occurred: ${errorMessage}. Please try again.`);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2 className="input-label">2. Define Topic</h2>
      <div className="input-group">
        <input
          type="text"
          value={topic}
          onChange={(e) => setTopic(e.target.value)}
          placeholder="e.g., The Future of AI in Healthcare"
          className="input-field"
        />
      </div>
      <button
        type="button"
        onClick={handleResearch}
        disabled={loading || !topic}
        className="btn-primary"
      >
        {loading ? 'Researching...' : 'Generate Content'}
      </button>
      {error && <p style={{ color: 'red' }}>{error}</p>}
    </div>
  );
}
