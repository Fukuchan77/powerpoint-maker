import asyncio
import json
from typing import List, Optional

from beeai_framework.backend.message import UserMessage

# ... (imports remain)
from beeai_framework.tools.search.duckduckgo import DuckDuckGoSearchTool

from app.core.llm import get_llm
from app.schemas import LayoutInfo, PresentationPlan, SlideContent

try:
    from duckduckgo_search import DDGS

    DDGS_AVAILABLE = True
except ImportError:
    DDGS_AVAILABLE = False
    print("duckduckgo_search not available")

try:
    from docling.document_converter import DocumentConverter

    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False
    print("Docling not available")


class ResearchAgent:
    def __init__(self):
        self.tool = DuckDuckGoSearchTool()
        try:
            self.llm = get_llm()
            self.enabled = True
        except Exception as e:
            print(f"LLM initialization failed: {e}")
            self.enabled = False

        if DOCLING_AVAILABLE:
            self.converter = DocumentConverter()

    def select_layout(self, content: SlideContent, layouts: List[LayoutInfo]) -> int:
        """Select the best layout index for the content based on heuristics"""
        if not layouts:
            return content.layout_index  # Keep default if no layouts provided

        # Heuristics
        has_image = bool(content.image_url or content.image_caption)
        has_bullets = bool(content.bullet_points or content.bullets)

        # Refine title heuristic: It's a title only if explicitly stated or default index 0,
        # BUT it must NOT have substantial content (bullets or image)
        is_title = ("Intro" in content.title or content.layout_index == 0) and not has_bullets and not has_image

        best_layout = content.layout_index
        best_score = -1

        for layout in layouts:
            score = 0

            # Identify placeholders
            has_title_ph = False
            has_body_ph = False
            has_pic_ph = False

            for ph in layout.placeholders:
                if ph.type == "TITLE" or ph.type == "CENTER_TITLE":
                    has_title_ph = True
                if ph.type == "BODY":
                    has_body_ph = True
                if ph.type == "PICTURE":
                    has_pic_ph = True

            # Scoring
            if is_title and has_title_ph and not has_body_ph:
                score += 5

            if has_image and has_pic_ph:
                score += 10
            elif has_image and not has_pic_ph:
                score -= 5  # Penalize layouts without picture if we have one

            if has_bullets and has_body_ph:
                score += 5

            if score > best_score:
                best_score = score
                best_layout = layout.index

        return best_layout

    async def research(self, topic: str, layouts: Optional[List[LayoutInfo]] = None) -> List[SlideContent]:
        """
        Conduct deep research on the topic and return structured slide content.
        """
        if not self.enabled:
            return self._mock_research(topic)

        print(f"Starting research on: {topic}")

        # 1. Search
        search_results = await self.tool.run({"query": topic, "count": 3})

        # 2. Visit and Extract Content (Simplified Deep Research)
        combined_context = ""
        print(f"Found {len(search_results.results)} search results. Visiting pages...")

        tasks = []
        for res in search_results.results:
            url = res.url
            if url:
                tasks.append(self._fetch_content(url))

        contents = await asyncio.gather(*tasks)

        for content in contents:
            if content:
                combined_context += content + "\n\n---\n\n"

        # If no content found, fallback to snippets
        if not combined_context.strip():
            print("Could not fetch full content, falling back to search snippets")
            combined_context = "\n".join([r.description for r in search_results.results])

        # 3. Synthesize with LLM
        prompt = f"""
        You are a PowerPoint presentation generator.
        Based on the following research content about "{topic}", generate a structured presentation plan.

        The research content is:
        {combined_context[:20000]}

        Generate exactly 3 slides:
        1. Introduction
        2. Key Features/Deep Dive
        3. Future/Conclusion

        Output **ONLY** valid JSON matching this structure:
        {{
            "topic": "{topic}",
            "slides": [
                {{
                    "layout_index": 0, // Placeholder, will be optimized
                    "title": "Slide Title",
                    "bullets": [ // Preferred over bullet_points for hierarchy
                        {{ "text": "Main Point", "level": 0 }},
                        {{ "text": "Sub Point", "level": 1 }}
                    ],
                    "image_caption": "Description of an image relevant to this slide",
                    "chart": {{ // Optional, if data is suitable for visualization
                        "title": "Chart Title",
                        "type": "COLUMN_CLUSTERED", // or BAR_CLUSTERED, LINE, PIE
                        "categories": ["Cat1", "Cat2"],
                        "series": [
                            {{ "name": "Series 1", "values": [10, 20] }}
                        ]
                    }}
                }}
            ]
        }}
        """

        response = await self.llm.generate([UserMessage(content=prompt)])

        try:
            text_response = response.state.message.content
            if isinstance(text_response, list):
                text_response = "".join([c.text for c in text_response if hasattr(c, "text")])

            if "```json" in text_response:
                text_response = text_response.split("```json")[1].split("```")[0]
            elif "```" in text_response:
                text_response = text_response.split("```")[1].split("```")[0]

            data = json.loads(text_response)
            plan = PresentationPlan(**data)

            # Post-process: specific layout selection
            if layouts:
                print("Optimizing layout selection based on content and template capabilities...")
                for slide in plan.slides:
                    # Select best layout index
                    slide.layout_index = self.select_layout(slide, layouts)

            # Post-process: Image enrichment
            await self.enrich_slides_with_images(plan.slides)

            return plan.slides

        except Exception as e:
            print(f"Failed to parse LLM response: {e}")
            return self._mock_research(topic)

    async def _fetch_content(self, url: str) -> str:
        if not DOCLING_AVAILABLE:
            return ""
        try:
            print(f"Scraping: {url}")
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(None, lambda: self.converter.convert(url))
            return result.document.export_to_markdown()
        except Exception as e:
            print(f"Failed to fetch {url}: {e}")
            return ""

    def _search_images(self, query: str) -> str:
        """Search for an image URL using DuckDuckGo"""
        if not DDGS_AVAILABLE:
            return ""
        try:
            print(f"Searching image for: {query}")
            with DDGS() as ddgs:
                # keywords: query, max_results=1
                results = list(ddgs.images(query, max_results=1))
                if results and len(results) > 0:
                    return results[0]["image"]
        except Exception as e:
            print(f"Image search failed for {query}: {e}")
        return ""

    async def enrich_slides_with_images(self, slides: List[SlideContent]):
        """Find images for slides that have captions but no URLs"""
        for slide in slides:
            if slide.image_caption and not slide.image_url:
                # Run sync in executor to avoid blocking
                loop = asyncio.get_event_loop()
                url = await loop.run_in_executor(None, lambda s=slide: self._search_images(s.image_caption))
                if url:
                    slide.image_url = url
                    print(f"Found image for slide '{slide.title}': {url}")

    def _mock_research(self, topic: str) -> List[SlideContent]:
        return [
            SlideContent(
                layout_index=0,
                title=f"Introduction to {topic}",
                bullet_points=[f"Overview of {topic}", "Key importance", "Historical context"],
                image_caption="An introductory conceptual image",
            ),
            SlideContent(
                layout_index=1,
                title="Key Concepts",
                bullet_points=["Concept 1", "Concept 2", "Concept 3"],
                image_caption=None,
            ),
            SlideContent(
                layout_index=1,
                title="Future Trends",
                bullet_points=["Trend 1", "Trend 2", "Conclusion"],
                image_caption=None,
            ),
        ]
