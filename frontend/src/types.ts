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
