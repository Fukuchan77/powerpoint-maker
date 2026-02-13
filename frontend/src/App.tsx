import { lazy, Suspense, useState } from 'react';
import ErrorBoundary from './components/ErrorBoundary';
import type { ContentExtractionResult, SlideContent, TemplateAnalysisResult } from './types';

// Lazy load heavy components for better initial load performance
const TemplateUploader = lazy(() =>
  import('./components/TemplateUploader').then((module) => ({
    default: module.TemplateUploader,
  }))
);
const ContentInput = lazy(() =>
  import('./components/ContentInput').then((module) => ({
    default: module.ContentInput,
  }))
);
const Preview = lazy(() =>
  import('./components/Preview').then((module) => ({
    default: module.Preview,
  }))
);

// Loading fallback component
const LoadingFallback = () => (
  <div style={{ padding: '2rem', textAlign: 'center' }}>
    <div style={{ fontSize: '1.2rem', color: '#666' }}>Loading...</div>
  </div>
);

function App() {
  const [template, setTemplate] = useState<TemplateAnalysisResult | null>(null);
  const [slides, setSlides] = useState<SlideContent[] | null>(null);
  const [extractedContent, setExtractedContent] = useState<ContentExtractionResult | null>(null);

  const handleUseDefaultTemplate = () => {
    // Set a minimal template result for default template
    setTemplate({
      filename: 'default.pptx',
      template_id: 'default',
      masters: [
        {
          index: 0,
          name: 'Default Master',
          layouts: [
            { index: 0, name: 'Title Slide', placeholders: [] },
            { index: 1, name: 'Content Slide', placeholders: [] },
          ],
        },
      ],
    });
  };

  const handleContentExtracted = (result: ContentExtractionResult) => {
    setExtractedContent(result);
    // Auto-select default template if no template is selected yet
    if (!template) {
      handleUseDefaultTemplate();
    }
  };

  // Convert extracted slides to compatible SlideContent format
  const convertedExtractedSlides: SlideContent[] | undefined = extractedContent?.slides.map(
    (slide) => ({
      layout_index: slide.layout_index,
      title: slide.title || '',
      bullet_points: slide.bullet_points.map((bp) => bp.text),
      bullets: slide.bullet_points,
      image_url: slide.image_refs.length > 0 ? slide.image_refs[0] : null,
      chart: slide.chart
        ? {
            ...slide.chart,
            title: slide.title || '',
            type: slide.chart.chart_type,
          }
        : null,
    })
  );

  return (
    <ErrorBoundary>
      <div>
        <h1 style={{ marginBottom: '2rem' }}>AI PowerPoint Agent</h1>

        <ErrorBoundary>
          <Suspense fallback={<LoadingFallback />}>
            <TemplateUploader
              onAnalysisComplete={setTemplate}
              onUseDefault={handleUseDefaultTemplate}
              onContentExtracted={handleContentExtracted}
            />
          </Suspense>
        </ErrorBoundary>

        {extractedContent && (
          <div className="card" style={{ backgroundColor: '#f0fdf4', marginBottom: '1rem' }}>
            <h3 style={{ margin: 0 }}>Content Extracted</h3>
            <p style={{ margin: 0 }}>
              Source: {extractedContent.filename} ({extractedContent.slides.length} slides)
            </p>
            {extractedContent.warnings.length > 0 && (
              <div
                style={{
                  marginTop: '0.5rem',
                  fontSize: '0.9rem',
                  color: '#b91c1c',
                }}
              >
                <strong>Warnings:</strong>
                <ul style={{ margin: '0.25rem 0 0 1.2rem' }}>
                  {extractedContent.warnings.map((w, i) => (
                    // biome-ignore lint/suspicious/noArrayIndexKey: Warning list is static
                    <li key={i}>{w}</li>
                  ))}
                </ul>
              </div>
            )}
          </div>
        )}

        {template && (
          <>
            <div className="card" style={{ backgroundColor: '#e0f2fe' }}>
              <h3 style={{ margin: 0 }}>Template Loaded: {template.filename}</h3>
              <p style={{ margin: 0 }}>
                Detected {template.masters?.[0]?.layouts?.length ?? 0} layouts.
              </p>
            </div>

            <ErrorBoundary>
              <Suspense fallback={<LoadingFallback />}>
                <ContentInput
                  onContentGenerated={setSlides}
                  extractionId={extractedContent?.extraction_id}
                  extractedSlides={convertedExtractedSlides}
                />
              </Suspense>
            </ErrorBoundary>
          </>
        )}

        {template && slides && (
          <ErrorBoundary>
            <Suspense fallback={<LoadingFallback />}>
              <Preview slides={slides} template={template} />
            </Suspense>
          </ErrorBoundary>
        )}
      </div>
    </ErrorBoundary>
  );
}

export default App;
