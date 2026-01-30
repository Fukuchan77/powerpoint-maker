import { useState } from "react";
import axios from "axios";
import type { SlideContent } from "../types";

interface TopicInputProps {
  onContentGenerated: (slides: SlideContent[]) => void;
}

export function TopicInput({ onContentGenerated }: TopicInputProps) {
  const [topic, setTopic] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleResearch = async () => {
    if (!topic) return;
    setLoading(true);
    setError(null);

    try {
      const response = await axios.post("/api/research", null, {
        params: { topic }, // POST query param as per routes.py definition: async def research_topic(topic: str)
      });
      onContentGenerated(response.data);
    } catch (err) {
      setError("Failed to generate content. Please try again.");
      console.error(err);
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
        onClick={handleResearch}
        disabled={loading || !topic}
        className="btn-primary"
      >
        {loading ? "Researching..." : "Generate Content"}
      </button>
      {error && <p style={{ color: "red" }}>{error}</p>}
    </div>
  );
}
