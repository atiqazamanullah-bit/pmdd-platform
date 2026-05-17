from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from typing import List
import os

from backend.db.database import get_db
from backend.db.models import Project, AnalysisReport, User
from backend.api.deps import get_current_user
from backend.services.pdf_generator import generate_academic_pdf

router = APIRouter()

@router.get("/")
async def get_projects(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    stmt = select(Project).where(Project.owner_id == current_user.id).order_by(Project.created_at.desc())
    res = await db.execute(stmt)
    projects = res.scalars().all()
    
    return [
        {
            "id": p.id,
            "title": p.title,
            "keywords": p.keywords,
            "created_at": p.created_at
        } for p in projects
    ]

@router.get("/{project_id}/pdf")
async def download_pdf(project_id: str, current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    stmt = select(Project).where(Project.id == project_id, Project.owner_id == current_user.id)
    res = await db.execute(stmt)
    project = res.scalars().first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    stmt = select(AnalysisReport).where(AnalysisReport.project_id == project_id)
    res = await db.execute(stmt)
    report = res.scalars().first()
    
    if not report or report.status != "completed":
        raise HTTPException(status_code=400, detail="Report not ready")
        
    report_data = {
        "reliability": report.reliability_metrics,
        "findings": report.findings
    }
    
    os.makedirs("reports", exist_ok=True)
    pdf_path = os.path.join("reports", f"{project_id}.pdf")
    generate_academic_pdf(project_id, project.title, report_data, pdf_path)
    
    return FileResponse(pdf_path, media_type='application/pdf', filename=f"{project.title}_analysis.pdf")
