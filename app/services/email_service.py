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


async def send_interview_schedule_email(
    email_to: str,
    candidate_name: str,
    job_title: str,
    company_name: str,
    interview_time_str: str,
    meeting_link: str | None,
    location: str | None,
    notes: str | None,
    action: str = "created"  # "created" or "updated"
):
    """
    Hàm gửi email thông báo lịch phỏng vấn mới hoặc cập nhật
    """
    subject_action = "Lịch phỏng vấn mới" if action == "created" else "Cập nhật lịch phỏng vấn"
    subject = f"[{settings.PROJECT_NAME}] {subject_action} - Vị trí {job_title}"
    
    # Tạo HTML content với thiết kế cao cấp
    meeting_section = ""
    if meeting_link:
        meeting_section = f"""
        <tr>
            <td style="padding: 10px 0; font-weight: 600; color: #4b5563; vertical-align: top; width: 120px;">Đường link:</td>
            <td style="padding: 10px 0; vertical-align: top;"><a href="{meeting_link}" style="color: #4f46e5; text-decoration: none; font-weight: 600; word-break: break-all;">{meeting_link}</a></td>
        </tr>
        """
        
    location_section = ""
    if location and not meeting_link:
        location_section = f"""
        <tr>
            <td style="padding: 10px 0; font-weight: 600; color: #4b5563; vertical-align: top; width: 120px;">Địa điểm:</td>
            <td style="padding: 10px 0; color: #1f2937; vertical-align: top; line-height: 1.5;">{location}</td>
        </tr>
        """
        
    notes_section = ""
    if notes:
        notes_section = f"""
        <tr>
            <td style="padding: 10px 0; font-weight: 600; color: #4b5563; vertical-align: top; width: 120px;">Ghi chú:</td>
            <td style="padding: 10px 0; color: #4b5563; vertical-align: top; font-style: italic; line-height: 1.5;">{notes}</td>
        </tr>
        """
        
    cta_section = ""
    if meeting_link:
        cta_section = f"""
        <div style="text-align: center; margin: 35px 0 10px 0;">
            <a href="{meeting_link}" style="background-color: #4f46e5; color: #ffffff; padding: 14px 30px; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 15px; display: inline-block; box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.2);">
                VÀO PHÒNG PHỎNG VẤN
            </a>
        </div>
        """
    else:
        cta_section = f"""
        <div style="text-align: center; margin: 35px 0 10px 0;">
            <a href="{settings.BASE_URL}" style="background-color: #4f46e5; color: #ffffff; padding: 14px 30px; text-decoration: none; border-radius: 6px; font-weight: 600; font-size: 15px; display: inline-block; box-shadow: 0 4px 6px -1px rgba(79, 70, 229, 0.2);">
                XEM CHI TIẾT TẠI HỆ THỐNG
            </a>
        </div>
        """

    action_text = "một lịch phỏng vấn mới" if action == "created" else "sự thay đổi về lịch phỏng vấn"
    html_content = f"""
    <div style="font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f9fafb; padding: 40px 20px; color: #1f2937;">
        <div style="max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06); overflow: hidden;">
            <!-- Header -->
            <div style="background: linear-gradient(135deg, #4f46e5 0%, #6366f1 100%); padding: 30px 40px; text-align: center; color: #ffffff;">
                <h1 style="margin: 0; font-size: 24px; font-weight: 700; letter-spacing: -0.025em;">Thông Báo Lịch Phỏng Vấn</h1>
            </div>
            
            <!-- Content -->
            <div style="padding: 40px;">
                <p style="font-size: 16px; line-height: 1.6; margin-top: 0; color: #374151;">
                    Chào <strong>{candidate_name}</strong>,
                </p>
                <p style="font-size: 16px; line-height: 1.6; color: #4b5563;">
                    Chúng tôi xin thông báo rằng bạn có {action_text} cho vị trí <strong>{job_title}</strong> tại công ty <strong>{company_name}</strong>. Dưới đây là thông tin chi tiết:
                </p>
                
                <!-- Details Card -->
                <div style="background-color: #f3f4f6; border-radius: 8px; padding: 24px; margin: 30px 0;">
                    <table style="width: 100%; border-collapse: collapse; font-size: 15px;">
                        <tr>
                            <td style="padding: 10px 0; font-weight: 600; color: #4b5563; width: 120px; vertical-align: top;">Thời gian:</td>
                            <td style="padding: 10px 0; color: #1f2937; vertical-align: top;"><strong>{interview_time_str}</strong></td>
                        </tr>
                        <tr>
                            <td style="padding: 10px 0; font-weight: 600; color: #4b5563; vertical-align: top; width: 120px;">Hình thức:</td>
                            <td style="padding: 10px 0; color: #1f2937; vertical-align: top;">{"Trực tuyến (Online)" if meeting_link else "Trực tiếp (Offline)"}</td>
                        </tr>
                        {meeting_section}
                        {location_section}
                        {notes_section}
                    </table>
                </div>
                
                <!-- CTA Button -->
                {cta_section}
            </div>
            
            <!-- Footer -->
            <div style="background-color: #f9fafb; border-top: 1px solid #e5e7eb; padding: 25px 40px; text-align: center; font-size: 13px; color: #9ca3af;">
                <p style="margin: 0 0 8px 0;">Đây là email tự động gửi từ hệ thống <strong>{settings.PROJECT_NAME}</strong>.</p>
                <p style="margin: 0;">Vui lòng không trả lời trực tiếp email này.</p>
            </div>
        </div>
    </div>
    """

    message = MessageSchema(
        subject=subject,
        recipients=[email_to],
        body=html_content,
        subtype=MessageType.html
    )

    fm = FastMail(conf)
    try:
        await fm.send_message(message)
        print(f"Đã gửi email thông báo lịch phỏng vấn tới: {email_to}")
    except Exception as e:
        print(f"Lỗi gửi email thông báo lịch phỏng vấn: {str(e)}")