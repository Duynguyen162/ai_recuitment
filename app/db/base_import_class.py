from app.db.base import Base

from app.models.user import User
from app.models.companies import Company
from app.models.candidate_details import CandidateCertification, CandidateEducation , CandidateExperience ,CVUpload
from app.models.candidate_profiles import CandidateProfile
from app.models.job_posting import JobPosting
from app.models.applications import Application 
from app.models.ai_matching_scores import AiMatchingScore
from app.models.chat_messages import ChatMessage
from app.models.chat_sessions import ChatSession
from app.models.interview import Interview
from app.models.notifications import Notification
from app.models.ai_logs import AiLog, AiAlertConfig
from app.models.job_reports import JobReport
from app.models.company_follows import CompanyFollow
from app.models.parsed_cv_data import ParsedCVData
from app.models.ai_matching_cache import AiMatchingCache
from app.models.ai_matching_jobs import AiMatchingJob
