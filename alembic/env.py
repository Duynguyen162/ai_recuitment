import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# thêm vào sys.path để có thể import được các module trong thư mục app/
#----------------------------------------------#
# Thêm thư mục gốc vào sys.path để import được thư mục app/
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import Base và CÁC MODEL của bạn vào đây
from app.db.base import Base
from app.models.user import User  
from app.models.companies import Company, CompanyVerification, CompanyMember, CompanyDocument
from app.models.candidate_profiles import CandidateProfile
from app.models.candidate_details import CandidateExperience, CandidateEducation, CandidateCertification, CVUpload
from app.models.job_posting import JobPosting
from app.models.applications import Application
from app.models.ai_matching_scores import AiMatchingScore
from app.models.chat_messages import ChatMessage
from app.models.chat_sessions import ChatSession
from app.models.saved_jobs import SaveJob
from app.models.interview import Interview
from app.models.job_reports import JobReport
from app.models.company_follows import CompanyFollow
from app.models.notifications import Notification
from app.models.ai_logs import AiLog, AiAlertConfig
from app.models.subscription_plans import SubscriptionPlan
from app.models.ai_quotas import UserAiQuota, RoleAiQuota
from app.models.parsed_cv_data import ParsedCVData
from app.models.ai_matching_cache import AiMatchingCache
from app.models.ai_matching_jobs import AiMatchingJob
from app.models.payment_transactions import PaymentTransaction
#----------------------------------------------#


# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

from app.core.config import settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
# from myapp import mymodel
# target_metadata = mymodel.Base.metadata

target_metadata = Base.metadata # điều chỉnh node->Base.metadata 

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
