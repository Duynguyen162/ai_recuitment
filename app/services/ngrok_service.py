from app.core.config import settings
from app.core.logger import logger

try:
    from pyngrok import ngrok
except Exception:  # pragma: no cover
    ngrok = None


public_url: str | None = None


def start_ngrok() -> str | None:
    global public_url
    if not settings.NGROK_AUTOSTART:
        return None
    if ngrok is None:
        logger.warning("pyngrok not available. Please install dependencies.")
        return None

    if settings.NGROK_AUTHTOKEN:
        ngrok.set_auth_token(settings.NGROK_AUTHTOKEN)

    tunnel_kwargs = {}
    if settings.NGROK_DOMAIN:
        tunnel_kwargs["domain"] = settings.NGROK_DOMAIN

    tunnel = ngrok.connect(addr=settings.NGROK_PORT, bind_tls=True, **tunnel_kwargs)
    public_url = tunnel.public_url
    logger.info(f"Ngrok public URL: {public_url}")
    return public_url


def stop_ngrok() -> None:
    if ngrok is None:
        return
    try:
        ngrok.kill()
    except Exception:
        pass
