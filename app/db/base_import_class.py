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
