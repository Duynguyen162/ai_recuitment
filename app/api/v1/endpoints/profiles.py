import asyncio
import os
import sys
from fastapi import APIRouter, File, HTTPException
from sqlalchemy.orm import Session
from app.core.enum import RoleEnum
from app.crud.crud_candidate_detail import create_candidate_certification, create_candidate_cv, create_candidate_education, create_candidate_experience, delete_candidate_certification, delete_candidate_cv, delete_candidate_education, delete_candidate_experience, get_candidate_certification, get_candidate_cv, get_candidate_cv_by_id, get_candidate_education, get_candidate_experience, get_full_candidate_cv, update_candidate_certification, update_candidate_education, update_candidate_experience
from app.db.database import get_db
from app.models.user import User
from app.models.candidate_profiles import CandidateProfile
from app.models.candidate_details import CandidateExperience , CandidateEducation, CandidateCertification, CVUpload
from app.api.deps import get_current_user
from app.schemas.candidate_details_schema import CandidateExperienceCreate ,CandidateExperienceResponse
from app.schemas.candidate_details_schema import CandidateEducationCreate, CandidateEducationResponse
from app.schemas.candidate_profiles_schema import CandidateProfileResponse , CandidateProfileUpdate
from app.schemas.candidate_details_schema import CandidateCertificationCreate, CandidateCertificationResponse
from app.schemas.candidate_details_schema import CVUploadCreate, CVUploadResponse
from app.crud.crud_candidate_profile import get_candidate_profile, upsert_profile
from fastapi.responses import FileResponse
from app.schemas.base_schema import ResponseSchema
from app.api.deps import get_current_candidate_profile
from fastapi import UploadFile, File   
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, Response
from fastapi.responses import Response
from jinja2 import Environment, FileSystemLoader
from playwright.async_api import async_playwright
from urllib.parse import quote

router = APIRouter(tags=["Candidate Profile"])

@router.get("/profileCandidate", response_model = ResponseSchema[CandidateProfileResponse])
def get_profile(db: Session = Depends(get_db), 
                current_user: User = Depends(get_current_user),
                profile: CandidateProfile = Depends(get_current_candidate_profile)
               ): 
    # Chuyển đổi từ SQLAlchemy model ( 1 đối tượng) sang Pydantic model(kiểu json)
    profile_response = CandidateProfileResponse.model_validate(profile)

    return ResponseSchema(
        success=True,
        data=profile_response,
        error=None,
        meta=None
    )

@router.post("/profileCandidate", response_model = ResponseSchema[CandidateProfileResponse])
def update_profile(profile_in: CandidateProfileUpdate,
                db: Session = Depends(get_db), 
                current_user: User = Depends(get_current_user),
                profile: CandidateProfile = Depends(get_current_candidate_profile)
                ):   
    upsert_profile(db, current_user.id, profile_in)
    profile_response = CandidateProfileResponse.model_validate(profile)
    return ResponseSchema(
        success=True,
        data=profile_response,
        error=None,
        meta=None
    )
#=============================================================#
#====================== KINH NGHIỆM ==========================#
#=============================================================#
@router.get("/experiences",response_model = ResponseSchema[list[CandidateExperienceResponse]])
def get_experience(db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user),
                       profile: CandidateProfile = Depends(get_current_candidate_profile)):
    exp_detail = get_candidate_experience(db,profile)
    return ResponseSchema(
        success=True,
        data=exp_detail,
        error=None,
        meta=None
    )

@router.post("/experiences", response_model = ResponseSchema[CandidateExperienceResponse])
def create_experience(experience_in: CandidateExperienceCreate,
                       db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user),
                       profile: CandidateProfile = Depends(get_current_candidate_profile)
                       ):
    candidate_exp = create_candidate_experience(db, experience_in.model_dump(), profile.id) # truyền candidate_id vào để liên kết
    return ResponseSchema(
        success=True,
        data=CandidateExperienceResponse.model_validate(candidate_exp),
        error=None,
        meta=None
    )

@router.put("/experiences/{experience_id}", 
            response_model = ResponseSchema[CandidateExperienceResponse])
def update_experience(experience_id: int,
                    experience_in: CandidateExperienceCreate,
                    db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user),
                    profile: CandidateProfile = Depends(get_current_candidate_profile)
                       ):
    exp = update_candidate_experience(db, experience_id, experience_in.model_dump(), current_user) # truyền dữ liệu đã chuyển đổi thành dict
    return ResponseSchema(
        success=True,
        data=CandidateExperienceResponse.model_validate(exp),
        error=None,
        meta=None
    )

@router.delete("/experiences/{experience_id}")
def delete_experience(experience_id: int,
                       db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user),
                       profile: CandidateProfile = Depends(get_current_candidate_profile)
                       ):
    delete_candidate_experience(db, experience_id, current_user )
    return ResponseSchema(
        success=True,
        data=None,
        error=None,
        meta=None
    )
#=============================================================#
#====================== HỌC VẤN ==============================#
#=============================================================#
@router.get("/educations",response_model = ResponseSchema[list[CandidateEducationResponse]])
def get_education(db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user),
                       profile: CandidateProfile = Depends(get_current_candidate_profile)):
    edu_detail = get_candidate_education(db,profile)
    return ResponseSchema(
        success=True,
        data=edu_detail,
        error=None,
        meta=None
    )

@router.post("/educations", response_model = ResponseSchema[CandidateEducationResponse])
def create_education(education_in: CandidateEducationCreate,
                     db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user),
                     profile: CandidateProfile = Depends(get_current_candidate_profile)
                     ): 
    education = create_candidate_education(db, education_in.model_dump(), profile.id) # truyền candidate_id vào để liên kết
    return ResponseSchema(
        success=True,
        data=CandidateEducationResponse.model_validate(education),
        error=None,
        meta=None
    )
@router.put("/educations/{education_id}", response_model = ResponseSchema[CandidateEducationResponse])
def update_education(education_id: int,
                    education_in: CandidateEducationCreate,
                    db: Session = Depends(get_db),
                    current_user: User = Depends(get_current_user),
                    profile: CandidateProfile = Depends(get_current_candidate_profile)
                       ):
    education = update_candidate_education(db, education_id, education_in.model_dump(), current_user)
    return ResponseSchema(
        success=True,
        data=CandidateEducationResponse.model_validate(education),
        error=None,
        meta=None
    )
@router.delete("/educations/{education_id}")
def delete_education(education_id: int,
                     db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user),
                     profile: CandidateProfile = Depends(get_current_candidate_profile)
                     ):
    delete_candidate_education(db, education_id, current_user)
    return ResponseSchema(
        success=True,
        data=None,
        error=None,
        meta=None
    )

#=============================================================#
#====================== BẰNG CẤP ==============================#
#=============================================================#
@router.get("/certifications",response_model = ResponseSchema[list[CandidateCertificationResponse]])
def get_certification(db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user),
                       profile: CandidateProfile = Depends(get_current_candidate_profile)):
    exp_detail = get_candidate_certification(db,profile)
    return ResponseSchema(
        success=True,
        data=exp_detail,
        error=None,
        meta=None
    )

@router.post("/certifications", response_model = ResponseSchema[CandidateCertificationResponse])
def create_certification(certification_in: CandidateCertificationCreate,
                         db: Session = Depends(get_db),
                         current_user: User = Depends(get_current_user),
                         profile: CandidateProfile = Depends(get_current_candidate_profile)
                         ):  
    certification = create_candidate_certification(db, certification_in.model_dump(), profile.id) # truyền candidate_id vào để liên kết
    return ResponseSchema(
        success=True,
        data=CandidateCertificationResponse.model_validate(certification),
        error=None,
        meta=None
    )
@router.put("/certifications/{certification_id}", response_model = ResponseSchema[CandidateCertificationResponse])
def update_certification(certification_id: int,
                         certification_in: CandidateCertificationCreate,
                         db: Session = Depends(get_db),
                         current_user: User = Depends(get_current_user),
                         profile: CandidateProfile = Depends(get_current_candidate_profile)
                       ):
    
    certification = update_candidate_certification(db, certification_id, certification_in.model_dump(), current_user)
    return ResponseSchema(
        success=True,
        data=CandidateCertificationResponse.model_validate(certification),
        error=None,
        meta=None
    )
@router.delete("/certifications/{certification_id}")
def delete_certification(certification_id: int,
                         db: Session = Depends(get_db),
                         current_user: User = Depends(get_current_user),
                         profile: CandidateProfile = Depends(get_current_candidate_profile)
                     ):
    delete_candidate_certification(db, certification_id, current_user)
    return ResponseSchema(
        success=True,
        data=None,
        error=None,
        meta=None
    )
#=============================================================#
#=========================== CV ==============================#
#=============================================================#


@router.get("/cv_upload",response_model = ResponseSchema[list[CVUploadResponse]])
def get_list_cv(db: Session = Depends(get_db),
                       current_user: User = Depends(get_current_user),
                       profile: CandidateProfile = Depends(get_current_candidate_profile)):
    """lấy danh sách các cv """
    url_cv = get_candidate_cv(db,profile)
    return ResponseSchema(
        success=True,
        data=url_cv,
        error=None,
        meta=None
    )

@router.get("/cv_upload/{cv_id}/view")
def view_cv_file(
    cv_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    profile: CandidateProfile = Depends(get_current_candidate_profile)
):
    cv = get_candidate_cv_by_id(db, profile, cv_id)
    file_path = cv.file_url 
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File không tồn tại trên server")

    return FileResponse(
        path=file_path, 
        filename=cv.file_name,
        # Bật Expose Headers để Frontend đọc được định dạng file
        headers={"Access-Control-Expose-Headers": "Content-Disposition"} 
    )

async def generate_pdf_from_html(html: str):
    """Convert HTML to PDF using Playwright"""
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    browser = None
    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch()
            page = await browser.new_page()
            
            # Set viewport để layout đúng
            await page.set_viewport_size({"width": 1200, "height": 1600})
            
            await page.set_content(html, wait_until="networkidle")
            
            pdf = await page.pdf(
                format="A4",
                print_background=True,  
                margin={"top": "10mm", "right": "10mm", "bottom": "10mm", "left": "10mm"},
                display_header_footer=False
            )
            await browser.close()
            return pdf
    except Exception as e:
        if browser:
            await browser.close()
        raise HTTPException(status_code=500, detail=f"Lỗi tạo PDF: {str(e)}")


@router.get("/export_cv")
async def export_cv_pdf(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    profile: CandidateProfile = Depends(get_current_candidate_profile)
):
    """ api export ra cv theo fomat của hệ thống"""
    full_profile = get_full_candidate_cv(db, profile.id)
    
    if not full_profile:
        raise HTTPException(status_code=404, detail="Không tìm thấy CV")

    context = {
        "full_name": full_profile.full_name or "Unknown",
        "phone": full_profile.phone or "",
        "email": current_user.email,
        "bio": full_profile.bio or "",
        "avatar_url": full_profile.avatar_url,

        "links": {
            "github": full_profile.github_url or "",
            "linkedin": full_profile.linkedin_url or "",
            "portfolio": full_profile.portfolio_url or "",
        },

        "skill_tags": full_profile.skill_tags or [],
        "years_of_experience": full_profile.years_of_experience or 0,

        "experiences": [
            {
                "company_name": exp.company_name,
                "job_title": exp.job_title, 
                "description": exp.description,
            }
            for exp in (full_profile.experiences or [])
        ],

        "educations": [
            {
                "institution_name": edu.institution_name,
                "major": edu.major,
                "degree": edu.degree,
            }
            for edu in (full_profile.educations or [])
        ],

        "certifications": [
            {
                "name": cert.name,
                "issuer": cert.issuer,
            }
            for cert in (full_profile.certifications or [])
        ],
    }

    try:
        # Render HTML
        env = Environment(loader=FileSystemLoader("app/templates"))
        template = env.get_template("cv_template.html")
        html_out = template.render(context)

        # Convert to PDF
        pdf_bytes = await generate_pdf_from_html(html_out)
        
        filename = f"CV_{full_profile.full_name}.pdf"
        safe_filename = quote(filename, safe='')
        
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename*=UTF-8\'\'{safe_filename}'
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lỗi xuất CV: {str(e)}")

@router.post("/cv_upload", response_model = ResponseSchema[CVUploadResponse])
def create_cv_upload(file: UploadFile = File(...),
                     db: Session = Depends(get_db),
                     current_user: User = Depends(get_current_user),
                     profile: CandidateProfile = Depends(get_current_candidate_profile)
                     ):
    cv_record = create_candidate_cv(db, file, profile.id, profile.user_id)
    return ResponseSchema(
        success=True,
        data=CVUploadResponse.model_validate(cv_record),
        error=None,
        meta=None
    )

@router.delete("/cv_upload/{cv_upload_id}")
def delete_cv_upload(cv_upload_id: int,
                         db: Session = Depends(get_db),
                         current_user: User = Depends(get_current_user),
                         profile: CandidateProfile = Depends(get_current_candidate_profile)
                     ):
    delete_candidate_cv(db,cv_upload_id,current_user)
    return ResponseSchema(
        success=True,
        data=None,
        error=None,
        meta=None
    )
