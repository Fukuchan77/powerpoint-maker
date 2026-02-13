import axios from 'axios';
import { useState } from 'react';
import type { AnalysisMode, ContentExtractionResult, TemplateAnalysisResult } from '../types';

interface TemplateUploaderProps {
  onAnalysisComplete: (result: TemplateAnalysisResult) => void;
  onContentExtracted?: (result: ContentExtractionResult) => void;
  onUseDefault: () => void;
}

export function TemplateUploader({
  onAnalysisComplete,
  onContentExtracted,
  onUseDefault,
}: TemplateUploaderProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [mode, setMode] = useState<AnalysisMode>('template');

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;

    const file = e.target.files[0];
    const formData = new FormData();
    formData.append('file', file);

    setLoading(true);
    setError(null);

    try {
      if (mode === 'content') {
        // Extract content from PPTX
        const response = await axios.post<ContentExtractionResult>(
          `/api/extract-content?mode=${mode}`,
          formData,
          { headers: { 'Content-Type': 'multipart/form-data' } }
        );
        if (onContentExtracted) {
          onContentExtracted(response.data);
        }
      } else {
        // Analyze template structure
        const response = await axios.post<TemplateAnalysisResult>(
          '/api/analyze-template',
          formData,
          { headers: { 'Content-Type': 'multipart/form-data' } }
        );
        onAnalysisComplete(response.data);
      }
    } catch (err) {
      setError(
        `Failed to ${mode === 'content' ? 'extract content' : 'analyze template'}. Please try again.`
      );
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2 className="input-label">1. Upload PowerPoint Template</h2>

      {/* Mode Selection */}
      <div style={{ marginBottom: '1rem' }}>
        <label style={{ marginRight: '1rem' }}>
          <input
            type="radio"
            name="mode"
            value="template"
            checked={mode === 'template'}
            onChange={() => setMode('template')}
          />
          <span style={{ marginLeft: '0.5rem' }}>Template Only</span>
        </label>
        <label>
          <input
            type="radio"
            name="mode"
            value="content"
            checked={mode === 'content'}
            onChange={() => setMode('content')}
          />
          <span style={{ marginLeft: '0.5rem' }}>Extract Content</span>
        </label>
      </div>

      <input
        type="file"
        accept=".pptx"
        onChange={handleFileChange}
        className="input-field"
        disabled={loading}
      />

      {/* Default Template Button */}
      <button
        type="button"
        onClick={onUseDefault}
        className="btn-secondary"
        style={{ marginTop: '0.5rem' }}
        disabled={loading}
      >
        Use Default Template
      </button>

      {loading && <p>Processing...</p>}
      {error && <p style={{ color: 'red' }}>{error}</p>}
    </div>
  );
}
