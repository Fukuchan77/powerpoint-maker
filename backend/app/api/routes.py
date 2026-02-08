import asyncio
import os
import uuid
from typing import List, Optional

from fastapi import APIRouter, File, HTTPException, Query, Request, UploadFile
from fastapi.responses import FileResponse

from app import config
from app.core.logging import get_logger
from app.exceptions import MarkdownSyntaxError
from app.middleware.rate_limit import limiter
from app.schemas import (
    AnalysisMode,
    ContentExtractionResult,
    LayoutIntelligenceRequest,
    LayoutIntelligenceResponse,
    MarkdownParseRequest,
    MarkdownParseResponse,
    PresentationRequest,
    SlideContent,
    TemplateAnalysisResult,
)
from app.services.extractor import ContentExtractor
from app.services.generator import PresentationGenerator
from app.services.layout_intelligence import LayoutIntelligenceService, OverflowValidator
from app.services.markdown_parser import MarkdownParser
from app.services.research import ResearchAgent
from app.services.template import LayoutRegistry, TemplateAnalyzer
from app.utils.file_validation import get_safe_filename, validate_template_file

logger = get_logger(__name__)

router = APIRouter()
analyzer = TemplateAnalyzer()  # Still needed for direct call in analyze_template? Or better use registry there too?
# Let's use Registry for analyze_template too to pre-populate cache.
layout_registry = LayoutRegistry()


def find_template_by_id(template_id: str) -> Optional[str]:
    """Find template file path by template ID prefix"""
    upload_dir = config.UPLOAD_DIR
    # Look for files starting with template_id
    for file in upload_dir.glob(f"{template_id}_*.pptx"):
        return str(file)
    # Fallback to old format for backward compatibility
    old_format = upload_dir / f"{template_id}.pptx"
    if old_format.exists():
        return str(old_format)
    return None


@router.post("/analyze-template", response_model=TemplateAnalysisResult)
@limiter.limit("10/minute")
async def analyze_template(request: Request, file: UploadFile = File(...)):  # noqa: B008
    """Analyze PowerPoint template structure

    Args:
        request: FastAPI request object
        file: Uploaded PowerPoint template file

    Returns:
        Template analysis result with master slides and layouts

    Raises:
        HTTPException: If file validation, saving, or analysis fails
    """
    try:
        logger.info("analyze_template_started", filename=file.filename, content_type=file.content_type)

        # Validate file
        content = await validate_template_file(file)

        # Sanitize filename
        safe_filename = get_safe_filename(file.filename)

        # Generate unique ID for this template upload
        template_id = str(uuid.uuid4())
        stored_filename = f"{template_id}_{safe_filename}"
        stored_path = config.UPLOAD_DIR / stored_filename

        # Save validated file content
        try:
            with open(stored_path, "wb") as buffer:
                buffer.write(content)
            logger.info("template_saved", template_id=template_id, path=str(stored_path))
        except Exception as e:
            logger.error("template_save_failed", error=str(e), template_id=template_id)
            raise HTTPException(status_code=500, detail="Failed to save template file. Please try again.") from e

        # Analyze and cache via Registry
        try:
            result = layout_registry.get_or_analyze(str(stored_path), template_id)
            result.filename = file.filename

            logger.info(
                "template_analysis_success",
                template_id=template_id,
                master_count=len(result.masters) if result.masters else 0,
            )
            return result
        except Exception as e:
            logger.error("template_analysis_failed", error=str(e), template_id=template_id)
            # Clean up file on analysis failure
            if stored_path.exists():
                stored_path.unlink()
            raise HTTPException(
                status_code=500,
                detail="Failed to analyze template structure. Please ensure the file is a valid PowerPoint template.",
            ) from e

    except HTTPException:
        raise
    except Exception as e:
        logger.error("analyze_template_unexpected_error", error=str(e), error_type=type(e).__name__)
        raise HTTPException(
            status_code=500, detail="An unexpected error occurred while processing the template."
        ) from e


# ... (generator code unchanged) ...

researcher = ResearchAgent()


@router.post("/research", response_model=List[SlideContent])
@limiter.limit("10/minute")
async def research_topic(request: Request, topic: str, template_id: Optional[str] = None):
    """
    Research a topic and generate slide content.

    Args:
        request: FastAPI request object
        topic: The topic to research
        template_id: Optional ID of an uploaded template to structure the content for

    Returns:
        List[SlideContent]: A list of generated slides, each containing:
            - title: Slide title
            - bullet_points: List of strings (simple bullets)
            - bullets: Optional List[BulletPoint] (structured bullets with levels)
            - layout_index: Index of the layout to use from the template
            - image_url: Optional URL for an image
            - image_caption: Optional caption for the image
            - chart: Optional chart data
            - theme_color: Optional theme color
    """
    import traceback

    try:
        print(f"[API] Starting research for topic: '{topic}'")
        layouts = None
        if template_id:
            print(f"[API] Template ID provided: {template_id}")
            template_path = find_template_by_id(template_id)
            if template_path:
                print(f"[API] Template found at: {template_path}")
                analysis = layout_registry.get_or_analyze(template_path, template_id)
                if analysis.masters:
                    layouts = analysis.masters[0].layouts
                    print(f"[API] Loaded {len(layouts)} layouts from template")
            else:
                print(f"[API] Template not found for ID: {template_id}")

        print("[API] Calling research agent...")
        slides = await researcher.research(topic, layouts)
        print(f"[API] Research completed successfully. Generated {len(slides)} slides")

        # Type safety: handle both dict and object
        validated_slides = []
        for i, slide in enumerate(slides):
            # Convert dict to SlideContent
            if isinstance(slide, dict):
                slide_obj = SlideContent(**slide)
            else:
                slide_obj = slide

            # Log output
            print(f"[API] Slide {i + 1}: {slide_obj.title}")
            print(f"  - bullet_points: {slide_obj.bullet_points}")
            print(f"  - bullets: {slide_obj.bullets}")
            print(f"  - layout_index: {slide_obj.layout_index}")
            validated_slides.append(slide_obj)

        return validated_slides
    except Exception as e:
        print(f"[API ERROR] Research failed for topic '{topic}':")
        print(f"[API ERROR] Exception type: {type(e).__name__}")
        print(f"[API ERROR] Exception message: {str(e)}")
        print("[API ERROR] Full traceback:")
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e)) from e


generator = PresentationGenerator()


@router.post("/generate")
@limiter.limit("5/minute")
async def generate_presentation(request: Request, gen_request: PresentationRequest):
    """Generate a PowerPoint presentation from slide content"""
    try:
        print(f"[GENERATE] Received request with {len(gen_request.slides)} slides")
        for i, slide in enumerate(gen_request.slides):
            print(f"[GENERATE] Slide {i + 1}: {slide.title}")
            print(f"  - bullet_points: {slide.bullet_points}")
            print(f"  - bullets: {slide.bullets}")
            print(f"  - layout_index: {slide.layout_index}")

        # Determine template path
        template_path = None

        if gen_request.template_id:
            # Try to use template_id first
            template_path = find_template_by_id(gen_request.template_id)
            if template_path:
                # Found by ID, use it
                pass

        # Fallback to template_filename
        if not template_path:
            if os.path.isabs(gen_request.template_filename):
                if os.path.exists(gen_request.template_filename):
                    template_path = gen_request.template_filename
            else:
                # Check in upload directory
                potential_path = config.UPLOAD_DIR / gen_request.template_filename
                if potential_path.exists():
                    template_path = str(potential_path)

        # Fallback to default template [REQ-2.1]
        if not template_path:
            if config.DEFAULT_TEMPLATE_PATH.exists():
                template_path = str(config.DEFAULT_TEMPLATE_PATH)
            else:
                raise HTTPException(status_code=404, detail="Template file not found")

        # Generate presentation
        output_filename = f"generated_{uuid.uuid4()}.pptx"
        output_path = config.UPLOAD_DIR / output_filename

        generated_path = generator.generate(template_path, gen_request.slides, str(output_path))

        return FileResponse(
            generated_path,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            filename=output_filename,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}") from e


# === PPTX Enhancement API Endpoints ===

markdown_parser = MarkdownParser()


@router.post("/extract-content", response_model=ContentExtractionResult)
@limiter.limit("10/minute")
async def extract_content(
    request: Request,
    file: UploadFile = File(...),  # noqa: B008
    mode: AnalysisMode = Query(AnalysisMode.CONTENT),  # noqa: B008
):
    """Extract content from PPTX file [REQ-1.1.1~REQ-1.2.1]

    Args:
        request: FastAPI request object
        file: Uploaded PowerPoint file
        mode: Analysis mode (content or template)

    Returns:
        ContentExtractionResult with extracted slides, images, and warnings
    """
    try:
        # Validate file
        content = await validate_template_file(file)

        # Save temporarily
        temp_id = str(uuid.uuid4())
        temp_path = config.UPLOAD_DIR / f"temp_{temp_id}.pptx"
        temp_path.write_bytes(content)

        try:
            # Get base URL from request
            base_url = str(request.base_url).rstrip("/")
            extractor = ContentExtractor(base_url)
            result = await extractor.extract(temp_path, mode)
            return result
        finally:
            # Clean up temp file
            if temp_path.exists():
                temp_path.unlink()

    except HTTPException:
        raise
    except Exception as e:
        logger.error("extract_content_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Content extraction failed: {str(e)}") from e


@router.post("/parse-markdown", response_model=MarkdownParseResponse)
@limiter.limit("20/minute")
async def parse_markdown(request: Request, body: MarkdownParseRequest):
    """Parse Markdown text to slide content [REQ-3.1.1~REQ-3.2.2]

    Args:
        request: FastAPI request object
        body: MarkdownParseRequest with Markdown content

    Returns:
        MarkdownParseResponse with parsed slides and warnings

    Raises:
        HTTPException(400): If Markdown syntax is invalid [REQ-5.2]
        HTTPException(500): If parsing fails unexpectedly
    """
    try:
        if len(body.content) > config.MAX_MARKDOWN_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"Markdown content exceeds maximum size of {config.MAX_MARKDOWN_SIZE} bytes",
            )

        result = markdown_parser.parse(body.content)
        return result

    except MarkdownSyntaxError as e:
        # Return structured error response [REQ-5.2]
        logger.warning(
            "markdown_syntax_error",
            line=e.line,
            column=e.column,
            message=e.message,
        )
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "MARKDOWN_SYNTAX_ERROR",
                "message": e.message,
                "location": {"line": e.line, "column": e.column},
            },
        ) from e
    except HTTPException:
        raise
    except Exception as e:
        logger.error("parse_markdown_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Markdown parsing failed: {str(e)}") from e


@router.post("/layout-intelligence", response_model=LayoutIntelligenceResponse)
@limiter.limit("5/minute")
async def layout_intelligence_endpoint(request: Request, body: LayoutIntelligenceRequest):
    """Transform raw text into structured slides using AI-powered layout intelligence.

    This endpoint uses LLM-based analysis to:
    1. Structure raw text into logical slides with appropriate layouts
    2. Detect and resolve text overflow issues
    3. Map abstract layout types to template-specific layouts

    Args:
        request: FastAPI request object
        body: LayoutIntelligenceRequest with text and optional template_id

    Returns:
        LayoutIntelligenceResponse with structured slides and warnings

    Raises:
        HTTPException(404): If template not found
        HTTPException(422): If LLM response validation fails
        HTTPException(504): If processing times out
        HTTPException(500): If processing fails unexpectedly
    """
    try:
        logger.info(
            "layout_intelligence_started",
            text_length=len(body.text),
            template_id=body.template_id,
        )

        # Resolve template path
        template_path: Optional[str] = None
        if body.template_id:
            template_path = find_template_by_id(body.template_id)
            if not template_path:
                raise HTTPException(
                    status_code=404,
                    detail=f"Template not found for ID: {body.template_id}",
                )
        else:
            # Use default template
            if not config.DEFAULT_TEMPLATE_PATH.exists():
                raise HTTPException(
                    status_code=404,
                    detail="Default template not found. Please upload a template.",
                )
            template_path = str(config.DEFAULT_TEMPLATE_PATH)

        # Analyze template to get layouts
        try:
            analysis = layout_registry.get_or_analyze(template_path, body.template_id or "default")
            if not analysis.masters or not analysis.masters[0].layouts:
                raise HTTPException(
                    status_code=500,
                    detail="Template has no layouts available",
                )
            template_layouts = analysis.masters[0].layouts
        except Exception as e:
            logger.error("template_analysis_failed", error=str(e), template_path=template_path)
            raise HTTPException(
                status_code=500,
                detail=f"Failed to analyze template: {str(e)}",
            ) from e

        # Process with layout intelligence service
        from app.services.layout_catalog import LayoutTemplateCatalog
        from app.services.layout_mapper import LayoutTypeMapper

        catalog = LayoutTemplateCatalog()
        mapper = LayoutTypeMapper()
        validator = OverflowValidator()
        service = LayoutIntelligenceService(catalog=catalog, mapper=mapper, validator=validator)

        try:
            # Wrap in asyncio.timeout for pipeline timeout
            async with asyncio.timeout(config.settings.layout_intelligence_timeout):
                result = await service.process(
                    text=body.text,
                    template_layouts=template_layouts,
                    timeout_seconds=float(config.settings.layout_intelligence_timeout),
                )

            logger.info(
                "layout_intelligence_success",
                slide_count=len(result.slides),
                template_id=body.template_id,
                warning_count=len(result.warnings),
            )

            return LayoutIntelligenceResponse(
                slides=result.slides,
                warnings=result.warnings,
            )

        except asyncio.TimeoutError as e:
            logger.error(
                "layout_intelligence_timeout",
                timeout=config.settings.layout_intelligence_timeout,
                template_id=body.template_id,
            )
            raise HTTPException(
                status_code=504,
                detail=f"Layout intelligence processing timed out after {config.settings.layout_intelligence_timeout}s",
            ) from e
        except ValueError as e:
            # Validation errors from LLM response
            logger.error("layout_intelligence_validation_error", error=str(e))
            raise HTTPException(
                status_code=422,
                detail=f"Invalid LLM response format: {str(e)}",
            ) from e
        except Exception as e:
            logger.error("layout_intelligence_processing_failed", error=str(e), error_type=type(e).__name__)
            raise HTTPException(
                status_code=500,
                detail=f"Layout intelligence processing failed: {str(e)}",
            ) from e

    except HTTPException:
        raise
    except Exception as e:
        logger.error("layout_intelligence_unexpected_error", error=str(e), error_type=type(e).__name__)
        raise HTTPException(
            status_code=500,
            detail="An unexpected error occurred during layout intelligence processing",
        ) from e


@router.get("/extracted-images/{extraction_id}/{image_id}")
async def get_extracted_image(extraction_id: str, image_id: str):
    """Serve extracted image by ID [REQ-1.1.3]

    Args:
        extraction_id: Extraction session ID
        image_id: Image ID within the extraction

    Returns:
        Image file response

    Raises:
        HTTPException: If image not found or expired
    """
    # Validate UUIDs to prevent path traversal
    try:
        uuid.UUID(extraction_id)
        uuid.UUID(image_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail="Invalid ID format") from e

    # Build path to image directory
    extraction_dir = config.EXTRACTED_IMAGES_DIR / extraction_id / "images"
    if not extraction_dir.exists():
        raise HTTPException(status_code=404, detail="Image not found or expired")

    # Find image file
    for img_file in extraction_dir.iterdir():
        if img_file.stem == image_id:
            return FileResponse(
                str(img_file),
                media_type=f"image/{img_file.suffix.lstrip('.')}",
            )

    raise HTTPException(status_code=404, detail="Image not found")
