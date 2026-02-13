export interface PlaceholderInfo {
  idx: number;
  name: string;
  type: string;
  width: number;
  height: number;
  left: number;
  top: number;
  accepts: string[];
}

export interface LayoutInfo {
  index: number;
  name: string;
  placeholders: PlaceholderInfo[];
}

export interface MasterInfo {
  index: number;
  name: string;
  layouts: LayoutInfo[];
}

export interface TemplateAnalysisResult {
  filename: string;
  template_id: string;
  masters: MasterInfo[];
}

export interface BulletPoint {
  text: string;
  level: number;
}

export interface ChartSeries {
  name: string;
  values: number[];
}

export interface ChartData {
  title: string;
  categories: string[];
  series: ChartSeries[];
  type: string; // "COLUMN_CLUSTERED", "BAR_CLUSTERED", "LINE", "PIE"
}

export interface SlideContent {
  layout_index: number;
  title: string;
  bullet_points: string[];
  bullets?: BulletPoint[];
  image_url?: string | null;
  image_caption?: string | null;
  chart?: ChartData | null;
  theme_color?: string | null;
}

export interface PresentationRequest {
  template_filename: string;
  template_id?: string;
  slides: SlideContent[];
  topic?: string;
}

// === PPTX Enhancement Types ===

export type AnalysisMode = 'content' | 'template';
export type ContentSource = 'web_search' | 'text_input' | 'markdown' | 'extracted';

export interface ExtractedImage {
  id: string;
  filename: string;
  url: string;
  slide_index: number;
  content_type: string;
}

export interface ExtractedChart {
  slide_index: number;
  chart_type: string;
  categories: string[];
  series: ChartSeries[];
}

export interface ExtractedSlideContent {
  slide_index: number;
  layout_index: number;
  title: string | null;
  body_text: string[];
  bullet_points: BulletPoint[];
  image_refs: string[];
  chart: ExtractedChart | null;
}

export interface ContentExtractionResult {
  extraction_id: string;
  filename: string;
  expires_at: string;
  slides: ExtractedSlideContent[];
  images: ExtractedImage[];
  warnings: string[];
}

export interface MarkdownParseRequest {
  content: string;
}

export interface MarkdownParseResponse {
  presentation_title: string | null;
  slides: SlideContent[];
  warnings: string[];
}
