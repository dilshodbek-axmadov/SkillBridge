from dataclasses import dataclass

from django.conf import settings
from django.core.mail import EmailMultiAlternatives


@dataclass(frozen=True)
class EmailService:
    """
    Thin email utility.

    Uses Django's email backend (configured in settings to point at SMTP / Mailtrap).
    """

    from_email: str = ""

    def send_otp(self, *, to_email: str, code: str) -> None:
        subject = "Your SkillBridge password reset code"
        text = (
            "We received a request to reset your SkillBridge password.\n\n"
            f"Your 6-digit code is: {code}\n\n"
            "This code expires in 15 minutes.\n"
            "If you didn't request this, you can ignore this email.\n"
        )

        from_email = self.from_email or getattr(settings, "DEFAULT_FROM_EMAIL", "")
        msg = EmailMultiAlternatives(subject=subject, body=text, from_email=from_email, to=[to_email])
        msg.send(fail_silently=False)

