"""Rendert den HTML-Digest und verschickt ihn per SMTP."""

import os
import smtplib
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

from jinja2 import Template

from .sources.base import JobPosting
from .static_site import person_page_url

TEMPLATE_PATH = Path("templates/email_digest.html")


def _pages_url_for(person_name: str) -> str:
    """Baut den Link zur eigenen GitHub-Pages-Unterseite dieser Person
    (docs/<slug>/, siehe static_site.py) — jede Person hat einen eigenen,
    von den anderen getrennten Link."""
    return person_page_url(os.environ["GITHUB_PAGES_URL"], person_name)


def render_digest(person_name: str, job_count: int) -> str:
    template = Template(TEMPLATE_PATH.read_text(encoding="utf-8"))
    return template.render(
        person_name=person_name, job_count=job_count, pages_url=_pages_url_for(person_name)
    )


def send_digest(to_email: str, person_name: str, jobs: list[JobPosting]) -> None:
    """Verschickt eine kurze Benachrichtigung mit Link zur GitHub-Pages-Seite
    (die eigentliche Job-Liste steht dort, nicht in der Mail)."""
    if not jobs:
        return

    html_body = render_digest(person_name, len(jobs))

    msg = MIMEMultipart("alternative")
    msg["Subject"] = Header(f"{len(jobs)} neue Jobvorschläge für dich", "utf-8")
    msg["From"] = os.environ["SMTP_FROM"]
    msg["To"] = to_email
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ["SMTP_PORT"])) as server:
        server.starttls()
        server.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
        server.send_message(msg)
