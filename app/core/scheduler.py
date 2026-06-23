from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timezone
from app.db.database import SessionLocal
from app.models.companies import Company
from app.core.logger import logger

scheduler = AsyncIOScheduler()

def check_and_reset_vip_status():
    """Hàm kiểm tra và reset trạng thái VIP cho công ty đã hết hạn"""
    db = SessionLocal()
    try:
        current_time = datetime.now(timezone.utc)
        
        # Lấy các công ty đang là VIP nhưng đã quá hạn
        expired_companies = db.query(Company).filter(
            Company.is_vip == True,
            Company.vip_expire_at <= current_time
        ).all()
        
        if expired_companies:
            for company in expired_companies:
                company.is_vip = False
                logger.info(f"Reset VIP status for company {company.id} - {company.name} due to expiration.")
            db.commit()
            
    except Exception as e:
        db.rollback()
        logger.error(f"Error in check_and_reset_vip_status: {e}")
    finally:
        db.close()

# Thêm job chạy định kỳ (mỗi ngày 1 lần)
scheduler.add_job(check_and_reset_vip_status, "interval", minutes=1440)