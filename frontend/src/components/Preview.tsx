import axios from "axios";
import { useState } from "react";
import type { SlideContent, TemplateAnalysisResult } from "../types";

interface PreviewProps {
  slides: SlideContent[];
  template: TemplateAnalysisResult;
}

export function Preview({ slides: initialSlides, template }: PreviewProps) {
  const [slides, setSlides] = useState(initialSlides);
  const [generating, setGenerating] = useState(false);
  const [downloadUrl, setDownloadUrl] = useState<string | null>(null);

  const handleGenerate = async () => {
    setGenerating(true);
    try {
      const response = await axios.post(
        "/api/generate",
        {
          template_filename: template.filename,
          template_id: template.template_id,
          slides: slides,
          topic: "User Topic", // Optional
        },
        {
          responseType: "blob",
        },
      );

      const url = window.URL.createObjectURL(new Blob([response.data]));
      setDownloadUrl(url);
    } catch (err) {
      console.error("Generation failed", err);
      alert("Generation failed");
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div className="card" data-testid="preview-section">
      <h2 className="input-label">3. Preview & Generate</h2>

      <div
        style={{
          maxHeight: "400px",
          overflowY: "auto",
          marginBottom: "1rem",
          border: "1px solid #ddd",
          padding: "1rem",
        }}
      >
        {slides.map((slide, idx) => (
          <div
            key={idx}
            style={{
              marginBottom: "1rem",
              paddingBottom: "1rem",
              borderBottom: "1px solid #eee",
            }}
          >
            <h3 style={{ margin: "0 0 0.5rem 0" }}>
              Slide {idx + 1}: {slide.title}
            </h3>
            <ul>
              {slide.bullet_points.map((point, pIdx) => (
                <li key={pIdx}>{point}</li>
              ))}
            </ul>
            <label style={{ fontSize: "0.8rem", color: "#666" }}>
              Layout Index:
              <input
                type="number"
                value={slide.layout_index}
                onChange={(e) => {
                  const val = parseInt(e.target.value);
                  if (!isNaN(val)) {
                    const newSlides = [...slides];
                    newSlides[idx].layout_index = val;
                    setSlides(newSlides);
                  }
                }}
                style={{ marginLeft: "0.5rem", width: "50px" }}
              />
            </label>
          </div>
        ))}
      </div>

      <div style={{ display: "flex", gap: "1rem", alignItems: "center" }}>
        <button
          onClick={handleGenerate}
          disabled={generating}
          className="btn-primary"
        >
          {generating ? "Generating PPTX..." : "Generate Presentation"}
        </button>

        {downloadUrl && (
          <a
            href={downloadUrl}
            download="presentation.pptx"
            className="btn-primary"
            style={{ textDecoration: "none", backgroundColor: "#10b981" }}
          >
            Download .pptx
          </a>
        )}
      </div>
    </div>
  );
}
