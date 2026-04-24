import os
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

router = APIRouter()

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
    # Giữ nguyên các Depends xác thực của bạn để bảo mật file
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
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.set_content(html)
        pdf = await page.pdf(
            format="A4",
            print_background=True,  
            margin={"top": "0", "right": "0", "bottom": "0", "left": "0"},
            display_header_footer=False
        )
        await browser.close()
        return pdf


@router.get("/export_cv")
async def export_cv_pdf(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    profile: CandidateProfile = Depends(get_current_candidate_profile)
):
    profile = get_full_candidate_cv(db, profile.id)
    
    if not profile:
        raise HTTPException(status_code=404, detail="Không tìm thấy CV")

    context = {
        "full_name": profile.full_name,
        "phone": profile.phone,
        "email": current_user.email,
        "bio": profile.bio,
        "avatar_url": profile.avatar_url,

        "links": {
            "github": profile.github_url,
            "linkedin": profile.linkedin_url,
            "portfolio": profile.portfolio_url,
        },

        "skill_tags": profile.skill_tags or [],
        "years_of_experience": profile.years_of_experience,

        "experiences": [
            {
                "company_name": exp.company_name,
                "job_title": exp.job_title, 
                "description": exp.description,
            }
            for exp in profile.experiences
        ],

        "educations": [
            {
                "institution_name": edu.institution_name,
                "major": edu.major,
                "degree": edu.degree,
            }
            for edu in profile.educations
        ],

        "certifications": [
            {
                "name": cert.name,
                "issuer": cert.issuer,
            }
            for cert in profile.certifications
        ],
    }

    # 2. Render HTML
    env = Environment(loader=FileSystemLoader("app/templates"))
    template = env.get_template("cv_template.html")
    html_out = template.render(context)

    # 3. Convert HTML → PDF
    pdf_bytes = await generate_pdf_from_html(html_out)
    
    filename = f"CV_{profile.full_name}.pdf"
    safe_filename = quote(filename)
    # 4. Return file
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{safe_filename}"
        }
    )

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
