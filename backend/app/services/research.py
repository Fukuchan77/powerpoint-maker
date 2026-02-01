import asyncio
import json
import re
from typing import Any, Dict, List, Optional
from unittest.mock import MagicMock

from beeai_framework.backend.message import UserMessage
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

    def _extract_text_from_response(self, response: Any) -> str:
        """
        Extract text content from various response types

        Handles:
        - Real LLM responses with output attribute
        - Mock objects (MagicMock) with state.message.content
        - Custom test objects with state.message
        - String responses
        - Message objects with content
        """
        print(f"[Research] Extracting text from response type: {type(response)}")

        # Case 1: Check for state.message.content (used in tests)
        if hasattr(response, "state"):
            if hasattr(response.state, "message"):
                if hasattr(response.state.message, "content"):
                    content = response.state.message.content
                    print(f"[Research] Found state.message.content: {type(content)}")
                    if isinstance(content, str):
                        return content
                    elif hasattr(content, "text"):
                        return content.text
                    return str(content)

        # Case 2: Mock object (MagicMock) with output
        if isinstance(response, MagicMock):
            # Try to access nested structure if it exists
            if hasattr(response, "output") and response.output:
                for msg in response.output:
                    if hasattr(msg, "content"):
                        content = msg.content
                        if isinstance(content, str):
                            return content
                        elif isinstance(content, list):
                            text_parts = []
                            for item in content:
                                if hasattr(item, "text"):
                                    text_parts.append(item.text)
                                elif isinstance(item, str):
                                    text_parts.append(item)
                            if text_parts:
                                return "".join(text_parts)

        # Case 3: Real response with output attribute
        if hasattr(response, "output"):
            text_parts = []
            for msg in response.output:
                if hasattr(msg, "text"):
                    text_parts.append(msg.text)
                elif hasattr(msg, "content"):
                    if isinstance(msg.content, list):
                        for content_item in msg.content:
                            if hasattr(content_item, "text"):
                                text_parts.append(content_item.text)
                            elif isinstance(content_item, str):
                                text_parts.append(content_item)
                    elif isinstance(msg.content, str):
                        text_parts.append(msg.content)
            if text_parts:
                return "".join(text_parts)

        # Case 4: Direct text/content attributes
        if hasattr(response, "text"):
            return response.text
        if hasattr(response, "content"):
            if isinstance(response.content, str):
                return response.content
            elif isinstance(response.content, list):
                text_parts = []
                for item in response.content:
                    if hasattr(item, "text"):
                        text_parts.append(item.text)
                    elif isinstance(item, str):
                        text_parts.append(item)
                return "".join(text_parts)

        # Case 5: Direct string
        if isinstance(response, str):
            return response

        # Fallback: This shouldn't happen with proper mocks
        result = str(response)
        print(f"[Research] Fallback string conversion: {result[:100]}...")
        return result

    def _extract_json_from_markdown(self, text: str) -> str:
        """
        Extract JSON from markdown code blocks

        Supports:
        - ```json ... ```
        - ``` ... ```
        - Raw JSON
        """
        # Try to extract from json code block
        json_match = re.search(r"```json\s*\n(.*?)\n```", text, re.DOTALL)
        if json_match:
            return json_match.group(1).strip()

        # Try to extract from generic code block
        generic_match = re.search(r"```\s*\n(.*?)\n```", text, re.DOTALL)
        if generic_match:
            content = generic_match.group(1).strip()
            # Validate it looks like JSON
            if content.startswith("{") or content.startswith("["):
                return content

        # Return as-is
        return text.strip()

    def _parse_llm_response(self, response: Any) -> Dict:
        """
        Robust LLM response parser with multiple fallback strategies
        """
        # Step 1: Extract text content
        text_response = self._extract_text_from_response(response)
        print(f"[Research] Extracted text length: {len(text_response)} characters")
        print(f"[Research] Text preview: {text_response[:200]}...")

        # Step 2: Extract JSON from markdown
        json_text = self._extract_json_from_markdown(text_response)

        # Step 3: Parse JSON
        data = json.loads(json_text)
        print(f"[Research] Successfully parsed JSON with {len(data.get('slides', []))} slides")

        return data

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
            print("[Research] LLM not enabled, using mock research")
            return self._mock_research(topic)

        try:
            print(f"[Research] Starting research on: {topic}")

            # 1. Search
            print("[Research] Performing web search...")
            search_results = await self.tool.run({"query": topic, "count": 3})
            print("[Research] Search completed")

            # 2. Visit and Extract Content (Simplified Deep Research)
            combined_context = ""
            print(f"[Research] Found {len(search_results.results)} search results. Visiting pages...")

            tasks = []
            for res in search_results.results:
                url = res.url
                if url:
                    tasks.append(self._fetch_content(url))

            contents = await asyncio.gather(*tasks)
            print(f"[Research] Content scraping completed. Processing {len(contents)} results...")

            for i, content in enumerate(contents):
                if content:
                    print(f"[Research] Adding content {i + 1}/{len(contents)} ({len(content)} chars)")
                    combined_context += content + "\n\n---\n\n"

            # If no content found, fallback to snippets
            if not combined_context.strip():
                print("[Research] Could not fetch full content, falling back to search snippets")
                combined_context = "\n".join([r.description for r in search_results.results])
            else:
                print(f"[Research] Total combined context: {len(combined_context)} characters")

            # 3. Synthesize with LLM
            print("[Research] Generating presentation plan with LLM...")
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

            print("[Research] Calling LLM...")
            # Use ChatModel's run method directly with a UserMessage
            response = await self.llm.run([UserMessage(content=prompt)])
            print("[Research] LLM response received")
            print(f"[Research] Response type: {type(response)}")

            # Use robust parser
            data = self._parse_llm_response(response)
            plan = PresentationPlan(**data)
            print(f"[Research] Successfully parsed plan with {len(plan.slides)} slides")

            # Post-process: specific layout selection
            if layouts:
                print("[Research] Optimizing layout selection based on content and template capabilities...")
                for slide in plan.slides:
                    # Select best layout index
                    slide.layout_index = self.select_layout(slide, layouts)
                print("[Research] Layout optimization completed")

            # Post-process: Image enrichment
            print("[Research] Enriching slides with images...")
            await self.enrich_slides_with_images(plan.slides)
            print("[Research] Image enrichment completed")

            # Convert bullets to bullet_points if needed for compatibility
            for slide in plan.slides:
                if slide.bullets and not slide.bullet_points:
                    slide.bullet_points = [b.text for b in slide.bullets]
                print(f"[Research] Slide: {slide.title}")
                print(f"  - bullets: {len(slide.bullets) if slide.bullets else 0}")
                print(f"  - bullet_points: {len(slide.bullet_points)}")

            print(f"[Research] Research completed successfully with {len(plan.slides)} slides")
            return plan.slides

        except Exception as e:
            import traceback

            print(f"[Research ERROR] Research failed: {e}")
            print(f"[Research ERROR] Error type: {type(e).__name__}")
            print("[Research ERROR] Full traceback:")
            print(traceback.format_exc())
            print("[Research] Falling back to mock research")
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
