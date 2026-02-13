import { useEffect, useState } from 'react';
import { parseMarkdown } from '../api/pptxEnhancement';
import type { SlideContent } from '../types';

interface MarkdownPreviewProps {
  markdownContent: string;
  debounceMs?: number;
}

/**
 * Live preview component for Markdown content
 * Shows real-time slide structure as user types
 */
export function MarkdownPreview({ markdownContent, debounceMs = 500 }: MarkdownPreviewProps) {
  const [slides, setSlides] = useState<SlideContent[]>([]);
  const [warnings, setWarnings] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Don't parse empty or whitespace-only content
    if (!markdownContent || !markdownContent.trim()) {
      setSlides([]);
      setWarnings([]);
      setError(null);
      setLoading(false);
      return;
    }

    setLoading(true);
    const timeoutId = setTimeout(async () => {
      try {
        const result = await parseMarkdown(markdownContent);
        setSlides(result.slides);
        setWarnings(result.warnings);
        setError(null);
      } catch (err: unknown) {
        // Don't show errors in preview - just clear slides
        setSlides([]);
        setWarnings([]);
        const errorMessage = err instanceof Error ? err.message : 'Parse error';
        setError(errorMessage);
      } finally {
        setLoading(false);
      }
    }, debounceMs);

    return () => clearTimeout(timeoutId);
  }, [markdownContent, debounceMs]);

  if (!markdownContent || !markdownContent.trim()) {
    return (
      <div style={{ padding: '1rem', color: '#666', fontStyle: 'italic' }}>
        Start typing Markdown to see a live preview...
      </div>
    );
  }

  return (
    <div
      style={{
        padding: '1rem',
        border: '1px solid #ddd',
        borderRadius: '4px',
        backgroundColor: '#f9f9f9',
      }}
    >
      <h3
        style={{
          marginTop: 0,
          marginBottom: '0.5rem',
          fontSize: '1rem',
          color: '#333',
        }}
      >
        Preview{' '}
        {loading && <span style={{ color: '#999', fontSize: '0.875rem' }}>(updating...)</span>}
      </h3>

      {error && (
        <div
          style={{
            color: '#999',
            fontSize: '0.875rem',
            marginBottom: '0.5rem',
          }}
        >
          Invalid Markdown - check syntax
        </div>
      )}

      {warnings.length > 0 && (
        <div style={{ marginBottom: '0.5rem' }}>
          {warnings.map((warning) => {
            return (
              <div
                key={warning}
                style={{
                  color: '#f90',
                  fontSize: '0.875rem',
                  marginBottom: '0.25rem',
                }}
              >
                ⚠️ {warning}
              </div>
            );
          })}
        </div>
      )}

      {slides.length === 0 && !error && (
        <div style={{ color: '#999', fontSize: '0.875rem' }}>
          No slides detected. Use ## for slide titles.
        </div>
      )}

      {slides.length > 0 && (
        <div>
          <div
            style={{
              fontSize: '0.875rem',
              color: '#666',
              marginBottom: '0.5rem',
            }}
          >
            {slides.length} slide{slides.length !== 1 ? 's' : ''} detected
          </div>
          {slides.map((slide, idx) => {
            return (
              <div
                key={`${slide.title}-${idx}`}
                style={{
                  marginBottom: '0.75rem',
                  padding: '0.75rem',
                  backgroundColor: '#fff',
                  border: '1px solid #e0e0e0',
                  borderRadius: '4px',
                }}
              >
                <div
                  style={{
                    fontWeight: 'bold',
                    marginBottom: '0.5rem',
                    color: '#333',
                  }}
                >
                  Slide {idx + 1}: {slide.title}
                </div>
                {slide.bullet_points && slide.bullet_points.length > 0 && (
                  <ul
                    style={{
                      margin: 0,
                      paddingLeft: '1.5rem',
                      fontSize: '0.875rem',
                    }}
                  >
                    {slide.bullet_points.map((bullet, bulletIdx) => {
                      return (
                        // biome-ignore lint/suspicious/noArrayIndexKey: List is static
                        <li key={bulletIdx} style={{ marginBottom: '0.25rem' }}>
                          {bullet}
                        </li>
                      );
                    })}
                  </ul>
                )}
                {slide.image_url && (
                  <div
                    style={{
                      marginTop: '0.5rem',
                      fontSize: '0.875rem',
                      color: '#666',
                    }}
                  >
                    🖼️ Image: {slide.image_url}
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
