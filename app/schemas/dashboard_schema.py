from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class DashboardStatsResponse(BaseModel):
    activeJobs: int
    newApplicants: int
    interviewsToday: int
    responseRate: int

class DashboardPendingApplication(BaseModel):
    id: int
    candidate_name: str
    job_title: str
    time: str

class DashboardUpcomingInterview(BaseModel):
    id: int
    candidate_name: str
    job_title: str
    time: str

class DashboardActiveJob(BaseModel):
    id: int
    title: str
    applicants_count: int
    ai_avg_score: int
    days_remaining: int
