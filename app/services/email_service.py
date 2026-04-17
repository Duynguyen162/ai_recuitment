from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from app.core.config import settings

# 1. Cấu hình kết nối tới máy chủ Gmail
conf = ConnectionConfig(
    MAIL_USERNAME=settings.MAIL_USERNAME,
    MAIL_PASSWORD=settings.MAIL_PASSWORD,
    MAIL_FROM=settings.MAIL_FROM,
    MAIL_PORT=settings.MAIL_PORT,
    MAIL_SERVER=settings.MAIL_SERVER,
    MAIL_STARTTLS=False,
    MAIL_SSL_TLS=True,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)
async def send_reset_password_email(email_to: str, reset_link: str):
    """
    Hàm thực tế gửi email khôi phục mật khẩu 
    """
    # Bạn có thể dùng HTML để email trông chuyên nghiệp hơn
    html_content = f"""
    <div style="font-family: Arial, sans-serif; padding: 20px; max-width: 600px;">
        <h2 style="color: #2c3e50;">Khôi phục mật khẩu</h2>
        <p>Chào bạn,</p>
        <p>Chúng tôi nhận được yêu cầu đặt lại mật khẩu cho tài khoản <strong>{email_to}</strong> trên hệ thống Tuyển dụng AI.</p>
        <p>Vui lòng click vào nút bên dưới để tiến hành đổi mật khẩu. Link này chỉ có hiệu lực trong vòng <strong>15 phút</strong>.</p>
        
        <div style="text-align: center; margin: 30px 0;">
            <a href="{reset_link}" style="background-color: #3498db; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-weight: bold;">
                ĐẶT LẠI MẬT KHẨU
            </a>
        </div>
        
        <p style="color: #7f8c8d; font-size: 12px;">Nếu bạn không yêu cầu đổi mật khẩu, vui lòng bỏ qua email này. Tài khoản của bạn vẫn an toàn.</p>
    </div>
    """

    # Tạo gói tin nhắn
    message = MessageSchema(
        subject="[AI Recruitment] Yêu cầu đặt lại mật khẩu",
        recipients=[email_to], # Gửi đến ai
        body=html_content,
        subtype=MessageType.html # Khai báo định dạng là HTML
    )

    # Khởi tạo FastMail và Gửi
    fm = FastMail(conf)
    try:
        await fm.send_message(message)
        print(f"Đã gửi email reset pass tới: {email_to}")
    except Exception as e:
        print(f"Lỗi gửi email: {str(e)}")