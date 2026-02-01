import { Suspense, lazy, useState } from "react";
import ErrorBoundary from "./components/ErrorBoundary";
import type { SlideContent, TemplateAnalysisResult } from "./types";

// Lazy load heavy components for better initial load performance
const TemplateUploader = lazy(() =>
  import("./components/TemplateUploader").then((module) => ({
    default: module.TemplateUploader,
  })),
);
const TopicInput = lazy(() =>
  import("./components/TopicInput").then((module) => ({
    default: module.TopicInput,
  })),
);
const Preview = lazy(() =>
  import("./components/Preview").then((module) => ({
    default: module.Preview,
  })),
);

// Loading fallback component
const LoadingFallback = () => (
  <div style={{ padding: "2rem", textAlign: "center" }}>
    <div style={{ fontSize: "1.2rem", color: "#666" }}>Loading...</div>
  </div>
);

function App() {
  const [template, setTemplate] = useState<TemplateAnalysisResult | null>(null);
  const [slides, setSlides] = useState<SlideContent[] | null>(null);

  return (
    <ErrorBoundary>
      <div>
        <h1 style={{ marginBottom: "2rem" }}>AI PowerPoint Agent</h1>

        <ErrorBoundary>
          <Suspense fallback={<LoadingFallback />}>
            <TemplateUploader onAnalysisComplete={setTemplate} />
          </Suspense>
        </ErrorBoundary>

        {template && (
          <>
            <div className="card" style={{ backgroundColor: "#e0f2fe" }}>
              <h3 style={{ margin: 0 }}>
                Template Loaded: {template.filename}
              </h3>
              <p style={{ margin: 0 }}>
                Detected {template.masters[0]?.layouts.length} layouts.
              </p>
            </div>

            <ErrorBoundary>
              <Suspense fallback={<LoadingFallback />}>
                <TopicInput onContentGenerated={setSlides} />
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
