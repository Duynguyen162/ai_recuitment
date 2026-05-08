from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    PROJECT_NAME: str = "AI Recruitment Platform"
    SECRET_KEY: str                         # dùng để tạo token
    ALGORITHM: str                          # dùng thuật toán nào để mã hóa token
    ACCESS_TOKEN_EXPIRE_MINUTES: int        # thời gian hết hạn của token
    BASE_URL: str
    # CẤU HÌNH EMAIL
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = ""
    MAIL_PORT: int = 465
    MAIL_SERVER: str = "smtp.gmail.com"
    
    OPENAI_API_KEY: str
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
    }
# khởi tạo đối tượng Settings để có thể truy cập các biến môi trường trong ứng dụng
settings = Settings()