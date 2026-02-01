import os
import uuid
from typing import List, Optional

from fastapi import APIRouter, File, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse

from app import config
from app.core.logging import get_logger
from app.middleware.rate_limit import limiter
from app.schemas import PresentationRequest, SlideContent, TemplateAnalysisResult
from app.services.generator import PresentationGenerator
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

        if not template_path:
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
