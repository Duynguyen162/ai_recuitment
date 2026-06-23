import hashlib
import json
import os
import socket
import time
from datetime import datetime, timedelta, timezone

import google.generativeai as genai
from sqlalchemy import and_, or_
from sqlalchemy.orm import joinedload
from sqlalchemy.exc import IntegrityError

from app.core.enum import AiMatchingJobStatusEnum, CvTypeEnum, ParseStatusEnum
from app.crud import crud_application
from app.db.database import SessionLocal
from app.models.ai_logs import AiLog
from app.models.ai_matching_cache import AiMatchingCache
from app.models.ai_matching_jobs import AiMatchingJob
from app.models.applications import Application
from app.models.candidate_details import CVUpload
from app.models.candidate_profiles import CandidateProfile
from app.models.parsed_cv_data import ParsedCVData
from app.core.logger import logger

PARSER_VERSION = "gemini_cv_parser_v1"
WORKER_ID = f"{socket.gethostname()}-pid-{os.getpid()}"
MAX_RETRIES = 5


class GeminiKeyManager:
    def __init__(self, filepath="secrets/gemini_keys.txt"):
        self.filepath = filepath
        self.keys = self._load_keys()
        self.current_index = 0

    def _load_keys(self):
        if not os.path.exists(self.filepath):
            raise FileNotFoundError(f"Khong tim thay file {self.filepath}")
        with open(self.filepath, "r", encoding="utf-8") as f:
            keys = [line.strip() for line in f if line.strip()]
        if not keys:
            raise ValueError(f"File {self.filepath} dang trong")
        return keys

    def get_current_key(self):
        return self.keys[self.current_index]

    def rotate_key(self):
        self.current_index = (self.current_index + 1) % len(self.keys)


key_manager: GeminiKeyManager | None = None


def _get_key_manager() -> GeminiKeyManager:
    global key_manager
    if key_manager is None:
        key_manager = GeminiKeyManager()
    return key_manager


def _canonicalize_json(data: dict | None) -> str:
    if not data:
        return ""
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _fingerprint(parsed_json: dict | None, raw_text: str | None) -> str:
    base = _canonicalize_json(parsed_json) or (raw_text or "")
    return hashlib.sha256(base.encode("utf-8")).hexdigest()


def _is_retryable_error(error_msg: str) -> bool:
    msg = error_msg.lower()
    return any(key in msg for key in ["429", "quota", "exhausted", "limit", "timeout", "temporar", "connection", "network"])


from app.services.ai_quota_service import consume_ai_tokens

def _gemini_json_response(prompt: str, model_name: str = "gemini-2.5-flash", db=None, application_id=None, service_type: str = "matching", user_id: int | None = None) -> dict:
    manager = _get_key_manager()
    max_retries = len(manager.keys)
    last_error = None
    start_time = time.perf_counter()
    
    for _ in range(max_retries):
        try:
            genai.configure(api_key=manager.get_current_key())
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json",
                    temperature=0.2,
                ),
            )
            
            processing_time_ms = int((time.perf_counter() - start_time) * 1000)
            usage = getattr(response, "usage_metadata", None)
            tokens = usage.total_token_count if usage else 0
            
            try:
                session = db if db else SessionLocal()
                ai_log = AiLog(
                    service_type=service_type,
                    application_id=application_id,
                    user_id=user_id,
                    tokens_used=tokens,
                    processing_time_ms=processing_time_ms,
                    is_error=False
                )
                session.add(ai_log)
                
                if user_id and tokens > 0:
                    consume_ai_tokens(session, user_id, tokens)
                    
                if db:
                    session.flush()
                else:
                    session.commit()
            except Exception as log_e:
                logger.error(f"Failed to save AiLog: {log_e}")
                if not db:
                    session.rollback()
            finally:
                if not db:
                    session.close()

            return json.loads(response.text)
        except Exception as e:
            last_error = e
            error_msg = str(e).lower()
            if "429" in error_msg or "quota" in error_msg or "exhausted" in error_msg or "limit" in error_msg:
                manager.rotate_key()
                continue
                
            processing_time_ms = int((time.perf_counter() - start_time) * 1000)
            try:
                session = db if db else SessionLocal()
                ai_log = AiLog(
                    service_type=service_type,
                    application_id=application_id,
                    user_id=user_id,
                    processing_time_ms=processing_time_ms,
                    is_error=True,
                    error_message=str(e)[:1000]
                )
                session.add(ai_log)
                if db:
                    session.flush()
                else:
                    session.commit()
            except Exception as log_e:
                logger.error(f"Failed to save error AiLog: {log_e}")
                if not db:
                    session.rollback()
            finally:
                if not db:
                    session.close()
            raise
    raise RuntimeError(f"Khong the goi Gemini voi tat ca API key: {last_error}")


def _build_profile_raw_text_and_json(candidate: CandidateProfile) -> tuple[str, dict]:
    exp_items = [
        {
            "company_name": exp.company_name,
            "job_title": exp.job_title,
            "description": exp.description or "",
        }
        for exp in candidate.experiences
    ]
    edu_items = [
        {
            "institution_name": edu.institution_name,
            "major": edu.major,
            "degree": edu.degree,
        }
        for edu in candidate.educations
    ]
    cert_items = [
        {
            "name": cert.name,
            "issuer": cert.issuer,
        }
        for cert in candidate.certifications
    ]

    raw_text_parts = [
        f"Ho ten: {candidate.full_name or ''}",
        f"Gioi thieu: {candidate.bio or ''}",
        f"Ky nang: {', '.join(candidate.skill_tags or [])}",
        "Kinh nghiem:",
    ]
    raw_text_parts.extend(
        [f"- {it['job_title']} tai {it['company_name']}: {it['description']}" for it in exp_items]
        or ["- Khong co"]
    )
    raw_text_parts.append("Hoc van:")
    raw_text_parts.extend(
        [f"- {it['degree']} {it['major']} tai {it['institution_name']}" for it in edu_items]
        or ["- Khong co"]
    )
    raw_text_parts.append("Chung chi:")
    raw_text_parts.extend([f"- {it['name']} ({it['issuer']})" for it in cert_items] or ["- Khong co"])

    parsed_json = {
        "full_name": candidate.full_name or "",
        "bio": candidate.bio or "",
        "skills": candidate.skill_tags or [],
        "experiences": exp_items,
        "educations": edu_items,
        "certifications": cert_items,
    }
    return "\n".join(raw_text_parts).strip(), parsed_json


def _extract_pdf_text(file_path: str) -> str:
    from pypdf import PdfReader

    reader = PdfReader(file_path)
    return "\n".join([(page.extract_text() or "") for page in reader.pages]).strip()


def _parse_uploaded_cv_to_json(raw_text: str, db=None, application_id=None) -> dict:
    parse_prompt = f"""
    Ban la he thong parser CV. Hay chuyen van ban CV thanh JSON sach de AI matching doc.
    Tra ve JSON dung schema sau va KHONG co text khac:
    {{
      "full_name": "string",
      "bio": "string",
      "skills": ["string"],
      "experiences": [{{"company_name":"string","job_title":"string","description":"string"}}],
      "educations": [{{"institution_name":"string","major":"string","degree":"string"}}],
      "certifications": [{{"name":"string","issuer":"string"}}]
    }}
    Neu thieu thong tin, tra ve chuoi rong hoac mang rong.

    CV TEXT:
    {raw_text}
    """
    return _gemini_json_response(parse_prompt, db=db, application_id=application_id)


def _upsert_parsed_cv_data(db, application: Application, include_ai_parse: bool) -> ParsedCVData:
    existing = db.query(ParsedCVData).filter(ParsedCVData.application_id == application.id).first()
    candidate = application.candidate_profile

    if application.cv_type == CvTypeEnum.profile:
        raw_text, parsed_json = _build_profile_raw_text_and_json(candidate)
        parse_status = ParseStatusEnum.success
        source_type = CvTypeEnum.profile
    else:
        cv = db.query(CVUpload).filter(
            CVUpload.id == application.cv_upload_id,
            CVUpload.candidate_id == application.candidate_id,
        ).first()
        if not cv:
            raise ValueError("Khong tim thay CV upload de parse")
        raw_text = _extract_pdf_text(cv.file_url)
        if include_ai_parse:
            parsed_json = _parse_uploaded_cv_to_json(raw_text, db=db, application_id=application.id)
            parse_status = ParseStatusEnum.success
        else:
            parsed_json = None
            parse_status = ParseStatusEnum.pending
        source_type = CvTypeEnum.uploaded_cv

    content_hash = hashlib.sha256((raw_text or "").encode("utf-8")).hexdigest() if raw_text else None
    if existing:
        existing.candidate_id = application.candidate_id
        existing.source_type = source_type
        existing.parse_status = parse_status if include_ai_parse or source_type == CvTypeEnum.profile else existing.parse_status
        if parsed_json is not None:
            existing.parsed_json = parsed_json
        existing.raw_text_snapshot = raw_text
        existing.parser_version = PARSER_VERSION
        existing.content_hash = content_hash
        db.commit()
        db.refresh(existing)
        return existing

    row = ParsedCVData(
        application_id=application.id,
        candidate_id=application.candidate_id,
        source_type=source_type,
        parse_status=parse_status,
        parsed_json=parsed_json,
        raw_text_snapshot=raw_text,
        parser_version=PARSER_VERSION,
        content_hash=content_hash,
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


def _score_prompt(job, parsed_json: dict) -> str:
    return f"""
    Ban la chuyen gia tuyen dung. Hay cham diem do phu hop giua CV da parse va Job.
    [JOB]
    - Tieu de: {job.title}
    - Tags: {job.tags}
    - Requirements: {job.requirements}
    [CV_JSON]
    {json.dumps(parsed_json, ensure_ascii=False)}
    Tra ve JSON duy nhat:
    {{
        "score": <0-100>,
        "strengths": ["..."],
        "weaknesses": ["..."],
        "explanation": "..."
    }}
    Bat buoc tieng Viet.
    """


def _copy_cache_to_application_score(db, application_id: int, cache: AiMatchingCache):
    score_data = {
        "score": cache.score,
        "strengths": cache.strengths or [],
        "weaknesses": cache.weaknesses or [],
        "explanation": cache.explanation,
    }
    crud_application.create_ai_matching_score(db, application_id, score_data)


def enqueue_ai_matching_job(application_id: int) -> None:
    db = SessionLocal()
    try:
        app_record = db.query(Application).options(
            joinedload(Application.job_posting),
            joinedload(Application.candidate_profile).joinedload(CandidateProfile.experiences),
            joinedload(Application.candidate_profile).joinedload(CandidateProfile.educations),
            joinedload(Application.candidate_profile).joinedload(CandidateProfile.certifications),
        ).filter(Application.id == application_id).first()
        if not app_record:
            logger.warning(f"[AI_MATCH] application_id={application_id} not found, skip enqueue")
            return

        parsed = _upsert_parsed_cv_data(db, app_record, include_ai_parse=False)
        cv_fingerprint = _fingerprint(parsed.parsed_json, parsed.raw_text_snapshot)

        cache = db.query(AiMatchingCache).filter(
            AiMatchingCache.job_id == app_record.job_id,
            AiMatchingCache.candidate_id == app_record.candidate_id,
            AiMatchingCache.cv_fingerprint == cv_fingerprint,
        ).first()
        if cache:
            logger.info(f"[AI_MATCH] cache hit at enqueue application_id={application_id}")
            _copy_cache_to_application_score(db, application_id, cache)
            return

        existing_job = db.query(AiMatchingJob).filter(
            AiMatchingJob.job_id == app_record.job_id,
            AiMatchingJob.candidate_id == app_record.candidate_id,
            AiMatchingJob.cv_fingerprint == cv_fingerprint,
            AiMatchingJob.status.in_([AiMatchingJobStatusEnum.queued, AiMatchingJobStatusEnum.processing]),
        ).first()
        if existing_job:
            logger.info(
                f"[AI_MATCH] duplicate active job skipped application_id={application_id} "
                f"job_id={app_record.job_id} candidate_id={app_record.candidate_id}"
            )
            return

        job = db.query(AiMatchingJob).filter(
            AiMatchingJob.application_id == application_id
        ).first()
        if job:
            job.job_id = app_record.job_id
            job.candidate_id = app_record.candidate_id
            job.cv_fingerprint = cv_fingerprint
            job.status = AiMatchingJobStatusEnum.queued
            job.attempt_count = 0
            job.error_message = None
            job.worker_id = None
            job.locked_at = None
            job.next_retry_at = datetime.now(timezone.utc)
        else:
            job = AiMatchingJob(
                application_id=application_id,
                job_id=app_record.job_id,
                candidate_id=app_record.candidate_id,
                cv_fingerprint=cv_fingerprint,
                status=AiMatchingJobStatusEnum.queued,
                attempt_count=0,
                next_retry_at=datetime.now(timezone.utc),
            )
            db.add(job)
        db.commit()
        logger.info(
            f"[AI_MATCH] enqueued application_id={application_id} "
            f"job_id={app_record.job_id} candidate_id={app_record.candidate_id}"
        )
    finally:
        db.close()


def _acquire_next_job(db) -> AiMatchingJob | None:
    now = datetime.now(timezone.utc)
    job = (
        db.query(AiMatchingJob)
        .filter(
            or_(
                AiMatchingJob.status == AiMatchingJobStatusEnum.queued,
                and_(
                    AiMatchingJob.status == AiMatchingJobStatusEnum.failed,
                    AiMatchingJob.next_retry_at <= now,
                ),
            )
        )
        .order_by(AiMatchingJob.created_at.asc())
        .with_for_update(skip_locked=True)
        .first()
    )
    if not job:
        return None

    job.status = AiMatchingJobStatusEnum.processing
    job.locked_at = now
    job.worker_id = WORKER_ID
    db.commit()
    db.refresh(job)
    return job


def _mark_job_done(db, job: AiMatchingJob):
    job.status = AiMatchingJobStatusEnum.done
    job.error_message = None
    job.locked_at = None
    db.commit()
    logger.info(f"[AI_MATCH] done queue_job_id={job.id} application_id={job.application_id}")


def _mark_job_failed(db, job: AiMatchingJob, error: Exception):
    job.attempt_count += 1
    job.error_message = str(error)[:1000]
    job.locked_at = None

    if _is_retryable_error(str(error)) and job.attempt_count < MAX_RETRIES:
        backoff_minutes = min(30, 2 ** job.attempt_count)
        job.status = AiMatchingJobStatusEnum.failed
        job.next_retry_at = datetime.now(timezone.utc) + timedelta(minutes=backoff_minutes)
        logger.warning(
            f"[AI_MATCH] retry queue_job_id={job.id} application_id={job.application_id} "
            f"attempt={job.attempt_count} next_retry_at={job.next_retry_at} error={error}"
        )
    else:
        job.status = AiMatchingJobStatusEnum.dead
        logger.error(
            f"[AI_MATCH] dead queue_job_id={job.id} application_id={job.application_id} "
            f"attempt={job.attempt_count} error={error}"
        )
    db.commit()


def _process_job(db, queue_job: AiMatchingJob):
    logger.info(f"[AI_MATCH] processing queue_job_id={queue_job.id} application_id={queue_job.application_id}")
    app_record = db.query(Application).options(
        joinedload(Application.job_posting),
        joinedload(Application.candidate_profile).joinedload(CandidateProfile.experiences),
        joinedload(Application.candidate_profile).joinedload(CandidateProfile.educations),
        joinedload(Application.candidate_profile).joinedload(CandidateProfile.certifications),
    ).filter(Application.id == queue_job.application_id).first()

    if not app_record:
        _mark_job_done(db, queue_job)
        return

    parsed_data = _upsert_parsed_cv_data(db, app_record, include_ai_parse=True)
    if not parsed_data.parsed_json:
        raise RuntimeError("Khong tao duoc parsed_json cho CV")

    cv_fingerprint = _fingerprint(parsed_data.parsed_json, parsed_data.raw_text_snapshot)
    queue_job.cv_fingerprint = cv_fingerprint
    db.commit()

    cache = db.query(AiMatchingCache).filter(
        AiMatchingCache.job_id == app_record.job_id,
        AiMatchingCache.candidate_id == app_record.candidate_id,
        AiMatchingCache.cv_fingerprint == cv_fingerprint,
    ).first()
    if cache:
        logger.info(f"[AI_MATCH] cache hit while processing queue_job_id={queue_job.id}")
        _copy_cache_to_application_score(db, app_record.id, cache)
        _mark_job_done(db, queue_job)
        return

    prompt = _score_prompt(app_record.job_posting, parsed_data.parsed_json)
    score_data = _gemini_json_response(prompt, db=db, application_id=queue_job.application_id)

    new_cache = AiMatchingCache(
        job_id=app_record.job_id,
        candidate_id=app_record.candidate_id,
        cv_fingerprint=cv_fingerprint,
        score=score_data.get("score"),
        strengths=score_data.get("strengths", []),
        weaknesses=score_data.get("weaknesses", []),
        explanation=score_data.get("explanation"),
    )
    db.add(new_cache)
    try:
        db.commit()
        db.refresh(new_cache)
    except IntegrityError:
        db.rollback()
        new_cache = db.query(AiMatchingCache).filter(
            AiMatchingCache.job_id == app_record.job_id,
            AiMatchingCache.candidate_id == app_record.candidate_id,
            AiMatchingCache.cv_fingerprint == cv_fingerprint,
        ).first()
        if not new_cache:
            raise

    _copy_cache_to_application_score(db, app_record.id, new_cache)
    _mark_job_done(db, queue_job)


def process_ai_matching_queue(batch_size: int = 5) -> int:
    processed = 0
    for _ in range(max(1, batch_size)):
        db = SessionLocal()
        try:
            queue_job = _acquire_next_job(db)
            if not queue_job:
                break
            try:
                _process_job(db, queue_job)
            except Exception as e:
                _mark_job_failed(db, queue_job, e)
            processed += 1
        finally:
            db.close()
    return processed


def enqueue_and_process_ai_matching(application_id: int):
    enqueue_ai_matching_job(application_id)
    process_ai_matching_queue(batch_size=1)
