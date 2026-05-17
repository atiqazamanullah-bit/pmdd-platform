from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
import shutil
import os
import json
import uuid

from backend.db.database import get_db
from backend.db.models import Project, AnalysisReport, User
from backend.api.deps import get_current_user
from orchestration.pipeline import run_analysis_pipeline

router = APIRouter()

@router.get("/")
async def root():
    return {"message": "Welcome to PMDD API"}

@router.post("/upload")
async def upload_corpus(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    corpus_name: str = Form(""),
    keywords: str = Form(""),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    project_id = str(uuid.uuid4())
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Prepend uuid to filename to ensure uniqueness
    safe_filename = f"{project_id}_{file.filename}"
    file_path = os.path.join(upload_dir, safe_filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Save project to DB
    new_project = Project(
        id=project_id,
        title=corpus_name or file.filename,
        keywords=keywords,
        owner_id=current_user.id
    )
    db.add(new_project)
    
    # Save initial pending report
    new_report = AnalysisReport(
        project_id=project_id,
        status="pending",
        reliability_metrics={},
        findings=[]
    )
    db.add(new_report)
    await db.commit()
    
    # We pass the safe_filename to pipeline because that's where it's stored on disk, 
    # but the pipeline will need project_id to update DB. Let's pass both.
    background_tasks.add_task(run_analysis_pipeline, project_id, safe_filename)
        
    return {
        "filename": file.filename, 
        "message": "Corpus uploaded and pipeline started",
        "corpusId": project_id
    }

@router.get("/reports/{corpus_id}")
async def fetch_report(
    corpus_id: str, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify ownership
    stmt = select(Project).where(Project.id == corpus_id, Project.owner_id == current_user.id)
    res = await db.execute(stmt)
    if not res.scalars().first():
        raise HTTPException(status_code=403, detail="Not authorized")
        
    stmt = select(AnalysisReport).where(AnalysisReport.project_id == corpus_id)
    result = await db.execute(stmt)
    report = result.scalars().first()
    
    if not report:
        return {"corpusId": corpus_id, "status": "pending"}
        
    return {
        "corpusId": corpus_id,
        "status": report.status,
        "reliability": report.reliability_metrics,
        "findings": report.findings
    }

