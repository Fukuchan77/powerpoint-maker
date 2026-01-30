import { useState } from "react";
import axios from "axios";
import type { TemplateAnalysisResult } from "../types";

interface TemplateUploaderProps {
  onAnalysisComplete: (result: TemplateAnalysisResult) => void;
}

export function TemplateUploader({
  onAnalysisComplete,
}: TemplateUploaderProps) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;

    const file = e.target.files[0];
    const formData = new FormData();
    formData.append("file", file);

    setLoading(true);
    setError(null);

    try {
      const response = await axios.post("/api/analyze-template", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      onAnalysisComplete(response.data);
    } catch (err) {
      setError("Failed to analyze template. Please try again.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="card">
      <h2 className="input-label">1. Upload PowerPoint Template</h2>
      <input
        type="file"
        accept=".pptx"
        onChange={handleFileChange}
        className="input-field"
        disabled={loading}
      />
      {loading && <p>Analyzing template...</p>}
      {error && <p style={{ color: "red" }}>{error}</p>}
    </div>
  );
}
