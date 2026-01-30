import { useState } from "react";
import { TemplateUploader } from "./components/TemplateUploader";
import { TopicInput } from "./components/TopicInput";
import { Preview } from "./components/Preview";
import type { TemplateAnalysisResult, SlideContent } from "./types";

function App() {
  const [template, setTemplate] = useState<TemplateAnalysisResult | null>(null);
  const [slides, setSlides] = useState<SlideContent[] | null>(null);

  return (
    <div>
      <h1 style={{ marginBottom: "2rem" }}>AI PowerPoint Agent</h1>

      <TemplateUploader onAnalysisComplete={setTemplate} />

      {template && (
        <>
          <div className="card" style={{ backgroundColor: "#e0f2fe" }}>
            <h3 style={{ margin: 0 }}>Template Loaded: {template.filename}</h3>
            <p style={{ margin: 0 }}>
              Detected {template.masters[0]?.layouts.length} layouts.
            </p>
          </div>

          <TopicInput onContentGenerated={setSlides} />
        </>
      )}

      {template && slides && <Preview slides={slides} template={template} />}
    </div>
  );
}

export default App;
