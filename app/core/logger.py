import logging
import sys

def setup_logger():
    logger = logging.getLogger("ai_recruitment")
    logger.setLevel(logging.DEBUG)
    
    # Định dạng log: Thời gian - Tên Module - Mức độ - Nội dung
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger

logger = setup_logger()