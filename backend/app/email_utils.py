import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

TEMPLATE_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "templates", "email.html")


def _parse_recipients(raw):
    if not raw:
        return []
    return [addr.strip() for addr in raw.split(",") if addr.strip()]


def send_notification_email(settings_dict: dict, old_ip: str, new_ip: str, domains: list):
    to_list = _parse_recipients(settings_dict.get("notification_email"))
    cc_list = _parse_recipients(settings_dict.get("notification_cc"))
    bcc_list = _parse_recipients(settings_dict.get("notification_bcc"))

    if not settings_dict.get("mail_host") or not to_list:
        raise ValueError("SMTP o destinatarios de notificación no configurados")

    with open(TEMPLATE_PATH, "r", encoding="utf-8") as f:
        html_content = f.read()

    html_content = html_content.replace("{{old_ip}}", old_ip or "N/A")
    html_content = html_content.replace("{{new_ip}}", new_ip or "N/A")
    domains_html = "\n".join([f"<li>{d}</li>" for d in domains])
    html_content = html_content.replace("{{domains_list}}", domains_html)

    app_name = settings_dict.get("mail_from_name") or "Cloudflare DDNS Updater"
    from_address = settings_dict.get("mail_from_address") or settings_dict.get("mail_username")

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[{app_name}] Cambio de IP detectado"
    msg["From"] = f"{app_name} <{from_address}>"
    msg["To"] = ", ".join(to_list)
    if cc_list:
        msg["Cc"] = ", ".join(cc_list)
    # El CCO nunca se añade como cabecera: solo va en la lista de destinatarios del envío SMTP
    msg.attach(MIMEText(html_content, "html"))

    all_recipients = to_list + cc_list + bcc_list

    port = int(settings_dict.get("mail_port") or 465)
    with smtplib.SMTP_SSL(settings_dict["mail_host"], port) as server:
        server.login(settings_dict["mail_username"], settings_dict["mail_password"])
        server.sendmail(from_address, all_recipients, msg.as_string())
