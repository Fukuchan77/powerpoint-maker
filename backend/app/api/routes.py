import os
import shutil
import uuid
from typing import List, Optional

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import FileResponse  # Import moved here for clarity

from app import config
from app.schemas import PresentationRequest, SlideContent, TemplateAnalysisResult
from app.services.generator import PresentationGenerator
from app.services.research import ResearchAgent
from app.services.template import LayoutRegistry, TemplateAnalyzer

router = APIRouter()
analyzer = TemplateAnalyzer()  # Still needed for direct call in analyze_template? Or better use registry there too?
# Let's use Registry for analyze_template too to pre-populate cache.
layout_registry = LayoutRegistry()


@router.post("/analyze-template", response_model=TemplateAnalysisResult)
async def analyze_template(file: UploadFile = File(...)):  # noqa: B008
    if not file.filename.endswith(".pptx"):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a .pptx file.")

    # Generate unique ID for this template upload
    template_id = str(uuid.uuid4())
    stored_filename = f"{template_id}.pptx"
    stored_path = config.UPLOAD_DIR / stored_filename

    # Save uploaded file
    try:
        with open(stored_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}") from e

    try:
        # Analyze and cache via Registry
        result = layout_registry.get_or_analyze(str(stored_path), template_id)
        result.filename = file.filename
        return result
    except Exception as e:
        # Clean up if analysis fails? debatable. For now keep it for debugging or delete.
        # os.remove(stored_path)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}") from e


# ... (generator code unchanged) ...

researcher = ResearchAgent()


@router.post("/research", response_model=List[SlideContent])
async def research_topic(topic: str, template_id: Optional[str] = None):
    try:
        layouts = None
        if template_id:
            # Check exist path first to be safe, or let registry handle it logic?
            # Registry 'get_or_analyze' expects path.
            # If we don't know path, we can construct it if we know convention.
            potential_path = config.UPLOAD_DIR / f"{template_id}.pptx"
            if potential_path.exists():
                analysis = layout_registry.get_or_analyze(str(potential_path), template_id)
                if analysis.masters:
                    layouts = analysis.masters[0].layouts

        content = await researcher.research(topic, layouts)
        return content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e


generator = PresentationGenerator()


@router.post("/generate")
async def generate_presentation(request: PresentationRequest):
    """Generate a PowerPoint presentation from slide content"""
    try:
        # Determine template path
        template_path = None

        if request.template_id:
            # Try to use template_id first
            potential_path = config.UPLOAD_DIR / f"{request.template_id}.pptx"
            if potential_path.exists():
                template_path = str(potential_path)

        # Fallback to template_filename
        if not template_path:
            if os.path.isabs(request.template_filename):
                if os.path.exists(request.template_filename):
                    template_path = request.template_filename
            else:
                # Check in upload directory
                potential_path = config.UPLOAD_DIR / request.template_filename
                if potential_path.exists():
                    template_path = str(potential_path)

        if not template_path:
            raise HTTPException(status_code=404, detail="Template file not found")

        # Generate presentation
        output_filename = f"generated_{uuid.uuid4()}.pptx"
        output_path = config.UPLOAD_DIR / output_filename

        generated_path = generator.generate(template_path, request.slides, str(output_path))

        return FileResponse(
            generated_path,
            media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
            filename=output_filename,
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}") from e
