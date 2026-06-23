from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    PROJECT_NAME: str = "AI Recruitment Platform"
    SECRET_KEY: str                         # dùng để tạo token
    ALGORITHM: str                          # dùng thuật toán nào để mã hóa token
    ACCESS_TOKEN_EXPIRE_MINUTES: int        # thời gian hết hạn của token
    BASE_URL: str
    FRONTEND_URL: str = "http://localhost:3000"
    # CẤU HÌNH EMAIL
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = ""
    MAIL_PORT: int = 465
    MAIL_SERVER: str = "smtp.gmail.com"
    
    OPENAI_API_KEY: str
    GOOGLE_API_KEY: str = ""
    SEPAY_IPN_API_KEY: str = ""
    SEPAY_BANK_NAME: str = ""
    SEPAY_BANK_ACCOUNT: str = ""
    SEPAY_ACCOUNT_HOLDER: str = ""
    SEPAY_QR_IMAGE_URL: str = ""
    NGROK_AUTOSTART: bool = False
    NGROK_AUTHTOKEN: str = ""
    NGROK_DOMAIN: str = ""
    NGROK_PORT: int = 8000
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }
# khởi tạo đối tượng Settings để có thể truy cập các biến môi trường trong ứng dụng
settings = Settings()
