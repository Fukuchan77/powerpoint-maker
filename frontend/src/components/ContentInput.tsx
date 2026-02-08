import { useState } from "react";
import type { SlideContent, ContentSource } from "../types";
import { parseMarkdown } from "../api/pptxEnhancement";
import axios from "axios";
import { MarkdownPreview } from "./MarkdownPreview";
import { TopicInput } from "./TopicInput";

interface ContentInputProps {
  onContentGenerated: (slides: SlideContent[]) => void;
  extractionId?: string;
  extractedSlides?: SlideContent[];
}

interface MarkdownSyntaxError {
  error_code: string;
  message: string;
  location: {
    line: number;
    column: number;
  };
}

/**
 * Component for displaying Markdown syntax errors with location info
 */
function SyntaxErrorDisplay({ error }: { error: MarkdownSyntaxError }) {
  return (
    <div
      data-testid="syntax-error"
      style={{
        backgroundColor: "#fee",
        border: "1px solid #faa",
        borderRadius: "4px",
        padding: "1rem",
        marginTop: "0.5rem",
      }}
    >
      <div
        style={{ fontWeight: "bold", color: "#c00", marginBottom: "0.5rem" }}
      >
        Markdown Syntax Error
      </div>
      <div style={{ marginBottom: "0.5rem" }}>{error.message}</div>
      <div style={{ fontSize: "0.875rem", color: "#666" }}>
        Location: Line {error.location.line}, Column {error.location.column}
      </div>
    </div>
  );
}

/**
 * Content input component supporting multiple content sources
 * [REQ-3.1.1~REQ-3.2.2, REQ-3.2.1]
 */
export function ContentInput({
  onContentGenerated,
  extractionId,
  extractedSlides,
}: ContentInputProps) {
  const [source, setSource] = useState<ContentSource>("web_search");
  const [markdownContent, setMarkdownContent] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [syntaxError, setSyntaxError] = useState<MarkdownSyntaxError | null>(
    null,
  );

  const handleMarkdownParse = async () => {
    if (!markdownContent.trim()) {
      setError("Please enter Markdown content");
      setSyntaxError(null);
      return;
    }

    setLoading(true);
    setError(null);
    setSyntaxError(null);

    try {
      const result = await parseMarkdown(markdownContent);

      if (result.warnings.length > 0) {
        console.warn("Markdown parsing warnings:", result.warnings);
      }

      onContentGenerated(result.slides);
    } catch (err: unknown) {
      console.error("Markdown parsing failed:", err);

      // Check if it's a structured syntax error from the API
      if (
        axios.isAxiosError(err) &&
        err.response?.status === 400 &&
        err.response?.data?.detail?.error_code === "MARKDOWN_SYNTAX_ERROR"
      ) {
        setSyntaxError(err.response.data.detail);
      } else {
        setError("Failed to parse Markdown. Please check your input.");
      }
    } finally {
      setLoading(false);
    }
  };

  const handleExtractedContent = () => {
    if (extractedSlides) {
      onContentGenerated(extractedSlides);
    }
  };

  return (
    <div className="card">
      <h2 className="input-label">2. Choose Content Source</h2>

      <div
        className="source-selector"
        data-testid="content-source-selector"
        style={{ marginBottom: "1rem" }}
      >
        <label style={{ marginRight: "1rem" }}>
          <input
            type="radio"
            name="source"
            value="web_search"
            data-testid="source-web-search"
            checked={source === "web_search"}
            onChange={() => setSource("web_search")}
          />
          <span style={{ marginLeft: "0.5rem" }}>Web Search</span>
        </label>
        <label style={{ marginRight: "1rem" }}>
          <input
            type="radio"
            name="source"
            value="markdown"
            data-testid="source-markdown"
            checked={source === "markdown"}
            onChange={() => setSource("markdown")}
          />
          <span style={{ marginLeft: "0.5rem" }}>Markdown Input</span>
        </label>
        {extractionId && extractedSlides && (
          <label>
            <input
              type="radio"
              name="source"
              value="extracted"
              data-testid="source-extracted"
              checked={source === "extracted"}
              onChange={() => setSource("extracted")}
            />
            <span style={{ marginLeft: "0.5rem" }}>Extracted Content</span>
          </label>
        )}
      </div>

      {source === "markdown" && (
        <>
          <textarea
            value={markdownContent}
            data-testid="markdown-textarea"
            onChange={(e) => {
              setMarkdownContent(e.target.value);
              // Clear errors when user starts typing
              setError(null);
              setSyntaxError(null);
            }}
            placeholder={`# Presentation Title

## Slide 1
- Bullet point 1
- Bullet point 2

## Slide 2
- More content here`}
            className="input-field"
            style={{ minHeight: "200px", fontFamily: "monospace" }}
          />
          <button
            onClick={handleMarkdownParse}
            disabled={loading || !markdownContent.trim()}
            className="btn-primary"
            data-testid="generate-from-markdown-btn"
            style={{ marginTop: "1rem" }}
          >
            {loading ? "Parsing..." : "Generate from Markdown"}
          </button>

          {/* Live Preview */}
          <div style={{ marginTop: "1rem" }}>
            <MarkdownPreview
              markdownContent={markdownContent}
              debounceMs={1000}
            />
          </div>
        </>
      )}

      {source === "extracted" && extractedSlides && (
        <div style={{ marginTop: "1rem" }}>
          <p>
            Using {extractedSlides.length} slides from extracted PPTX content
          </p>
          <button onClick={handleExtractedContent} className="btn-primary">
            Use Extracted Content
          </button>
        </div>
      )}

      {/* Show structured syntax error */}
      {syntaxError && <SyntaxErrorDisplay error={syntaxError} />}

      {/* Show generic error */}
      {error && <p style={{ color: "red" }}>{error}</p>}

      {source === "web_search" && (
        <div style={{ marginTop: "1rem" }}>
          <TopicInput onContentGenerated={onContentGenerated} />
        </div>
      )}
    </div>
  );
}
