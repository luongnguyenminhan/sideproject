"""OTP Utilities"""

import io
import os
import random
import secrets
import smtplib
import string
from datetime import datetime
from email import encoders
from email.header import Header
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from dotenv import load_dotenv
from pytz import timezone

from app.middleware.translation_manager import _
from app.utils.minio import minio_handler
from app.utils.pdf import MDToPDFConverter

load_dotenv()


class OTPUtils:
	"""Utils for OTP generation and email sending"""

	def __init__(self):
		"""Initialize OTP utils with SMTP credentials from environment"""
		self.smtp_username = os.getenv('SMTP_USERNAME', '')
		self.smtp_password = os.getenv('SMTP_PASSWORD', '')
		self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
		self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
		self.project_name = os.getenv('PROJECT_NAME', 'CGSEM')

	def GenerateOTP(self, length=6):
		"""Generate a random OTP code

		Args:
		    length (int): Length of OTP

		Returns:
		    str: Generated OTP
		"""
		# Generate OTP using digits only
		return ''.join(random.choices(string.digits, k=length))

	def send_email(self, otp, recipients):
		"""Send verification email with OTP

		Args:
		    otp (str): OTP code
		    recipients (list): List of recipient email addresses
		"""
		# Create message
		msg = MIMEMultipart()
		msg['From'] = self.smtp_username
		msg['To'] = ', '.join(recipients)
		msg['Subject'] = Header(f'{self.project_name} - {_("email_verification")}', 'utf-8')

		# Email body
		body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4A6FFF; color: white; padding: 10px; text-align: center; }}
                .content {{ padding: 20px; }}
                .otp {{ font-size: 24px; font-weight: bold; text-align: center; 
                       padding: 10px; margin: 20px 0; background-color: #f5f5f5; }}
                .footer {{ font-size: 12px; text-align: center; margin-top: 30px; color: #777; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>{self.project_name}</h2>
                </div>
                <div class="content">
                    <p>{_('email_verification_message')}</p>
                    <div class="otp">{otp}</div>
                    <p>{_('otp_valid_for_10_minutes')}</p>
                    <p>{_('ignore_if_not_requested')}</p>
                </div>
                <div class="footer">
                    <p>&copy; {self.project_name} - {_('do_not_reply')}</p>
                </div>
            </div>
        </body>
        </html>
        """

		msg.attach(MIMEText(body, 'html', 'utf-8'))

		# Connect to SMTP server and send email
		try:
			server = smtplib.SMTP(self.smtp_server, self.smtp_port)
			server.starttls()
			server.login(self.smtp_username, self.smtp_password)
			server.send_message(msg)
			server.quit()
			return True
		except Exception as e:
			print(f'[ERROR] Failed to send email: {e}')
			return False

	def send_reset_password_email(self, otp, recipients):
		"""Send password reset email with OTP

		Args:
		    otp (str): OTP code
		    recipients (list): List of recipient email addresses
		"""
		# Create message
		msg = MIMEMultipart()
		msg['From'] = self.smtp_username
		msg['To'] = ', '.join(recipients)
		msg['Subject'] = Header(f'{self.project_name} - {_("password_reset")}', 'utf-8')

		# Email body
		body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4A6FFF; color: white; padding: 10px; text-align: center; }}
                .content {{ padding: 20px; }}
                .otp {{ font-size: 24px; font-weight: bold; text-align: center; 
                       padding: 10px; margin: 20px 0; background-color: #f5f5f5; }}
                .footer {{ font-size: 12px; text-align: center; margin-top: 30px; color: #777; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>{self.project_name}</h2>
                </div>
                <div class="content">
                    <p>{_('password_reset_message')}</p>
                    <div class="otp">{otp}</div>
                    <p>{_('password_reset_code_valid_for_10_minutes')}</p>
                    <p>{_('ignore_if_not_requested')}</p>
                </div>
                <div class="footer">
                    <p>&copy; {self.project_name} - {_('do_not_reply')}</p>
                </div>
            </div>
        </body>
        </html>
        """

		msg.attach(MIMEText(body, 'html', 'utf-8'))

		# Connect to SMTP server and send email
		try:
			server = smtplib.SMTP(self.smtp_server, self.smtp_port)
			server.starttls()
			server.login(self.smtp_username, self.smtp_password)
			server.send_message(msg)
			server.quit()
			return True
		except Exception as e:
			print(f'[ERROR] Failed to send password reset email: {e}')
			return False

	def send_default_strong_password_email(self, password, recipients):
		"""Send default strong password email

		Args:
		    recipients (list): List of recipient email addresses
		"""
		# Create message
		msg = MIMEMultipart()
		msg['From'] = self.smtp_username
		msg['To'] = ', '.join(recipients)
		msg['Subject'] = Header(f'{self.project_name} - {_("default_strong_password")}', 'utf-8')

		# Email body
		body = f"""
        <html>
        <head>
            <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
            <style>
                body {{ background-color: #f4f4f7; margin: 0; padding: 0; }}
                .email-wrapper {{ width: 100%; background-color: #f4f4f7; padding: 20px 0; }}
                .email-container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background-color: #ffffff;
                    border-radius: 8px;
                    overflow: hidden;
                    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
                }}
                .email-header {{
                    background-color: #4A6FFF;
                    padding: 20px;
                    text-align: center;
                }}
                .email-header h2 {{
                    color: #ffffff;
                    margin: 0;
                    font-size: 24px;
                }}
                .email-body {{
                    padding: 30px;
                    font-family: Arial, sans-serif;
                    color: #51545E;
                    line-height: 1.6;
                }}
                .email-body p {{
                    margin: 16px 0;
                }}
                .email-body .password {{
                    font-size: 16px;
                    font-weight: bold;
                    background-color: #f0f4ff;
                    padding: 12px;
                    border-radius: 4px;
                    display: inline-block;
                }}
                .email-footer {{
                    padding: 20px;
                    text-align: center;
                    font-size: 12px;
                    color: #777777;
                }}
            </style>
        </head>
        <body>
            <table class="email-wrapper" width="100%" cellpadding="0" cellspacing="0">
                <tr>
                    <td align="center">
                        <table class="email-container" width="100%" cellpadding="0" cellspacing="0">
                            <tr>
                                <td class="email-header">
                                    <h2>{self.project_name}</h2>
                                </td>
                            </tr>
                            <tr>
                                <td class="email-body">
                                    <p>{_('default_strong_password_message')}</p>
                                    <p class="password">{_('your_default_strong_password')}: {password}</p>
                                    <p>{_('ignore_if_not_requested')}</p>
                                </td>
                            </tr>
                            <tr>
                                <td class="email-footer">
                                    &copy; {self.project_name} – {_('do_not_reply')}
                                </td>
                            </tr>
                        </table>
                    </td>
                </tr>
            </table>
        </body>
        </html>
        """

		msg.attach(MIMEText(body, 'html', 'utf-8'))

		# Connect to SMTP server and send email
		try:
			server = smtplib.SMTP(self.smtp_server, self.smtp_port)
			server.starttls()
			server.login(self.smtp_username, self.smtp_password)
			server.send_message(msg)
			server.quit()
			return True
		except Exception as e:
			print(f'[ERROR] Failed to send default strong password email: {e}')
			return False

	def send_meeting_note_to_email(self, email, note: str):
		# Create the email message
		msg = MIMEMultipart()
		msg['From'] = f'Meobeo.ai <{self.smtp_username}>'
		msg['To'] = email
		msg['Subject'] = 'Meeting Note from Meobeo.ai'

		# Generate a formatted date and time for the filename
		def get_formatted_date_time():
			now = datetime.now(timezone('Asia/Ho_Chi_Minh'))
			return now.strftime('%Y%m%d-%H%M%S')

		filename_base = f'MeetingNote-{get_formatted_date_time()}'
		pdf_filename = f'{filename_base}.pdf'

		# Convert markdown to PDF
		pdf_converter = MDToPDFConverter(markdown_text=note)
		pdf_bytes = pdf_converter.convert()

		# Upload PDF to MinIO
		object_name = f'meeting_notes/{pdf_filename}'
		pdf_io = io.BytesIO(pdf_bytes)
		pdf_url = None
		try:
			minio_handler.minio_client.put_object(
				bucket_name=minio_handler.bucket_name,
				object_name=object_name,
				data=pdf_io,
				length=len(pdf_bytes),
				content_type='application/pdf',
			)

			# Get the URL to the stored PDF file - consistent with transcript_service.py
			pdf_url = minio_handler.get_file_url(object_name)
		except Exception as e:
			print(f'Error uploading to MinIO: {str(e)}')

		# Attach the PDF to email
		attachment = MIMEBase('application', 'pdf')
		attachment.set_payload(pdf_bytes)
		encoders.encode_base64(attachment)
		attachment.add_header('Content-Disposition', f'attachment; filename={pdf_filename}')

		# Add HTML body content
		html_content = """<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Meeting Note by Meobeo.ai</title>
        </head>
        <body style="background-color: #f0f2f5; margin: 0; padding: 0; font-family: Arial, sans-serif;">
            <div style="width: 100%; max-width: 600px; margin: 50px auto; background-color: #fff; box-shadow: 0px 15px 25px rgba(0,0,0,0.1); border-radius: 10px; overflow: hidden;">
                <div style="background-color: #F37429; padding: 25px; color: #fff; font-size: 26px; font-weight: bold; text-align: center; letter-spacing: 1px;">
                    Meeting Note by Meobeo.ai
                </div>
                <div style="padding: 40px; text-align: center;">
                    <h1 style="color: #333; font-size: 24px; margin-bottom: 20px;">Ghi chú cuộc họp gần đây của bạn</h1>
                    <p style="font-size: 16px; color: #666; margin-bottom: 30px;">Chúng tôi đã đính kèm ghi chú dưới dạng file PDF để bạn dễ dàng tham khảo</p>
                </div>
                <div style="background-color: #f7f7f7; padding: 20px; text-align: center;">
                    <p style="font-size: 16px; font-weight: bold; color: #F37429; margin: 0;">Sent by Meobeo.ai</p>
                    <div style="margin-top: 10px;">
                        <a href="https://www.facebook.com/profile.php?id=61564246875319" style="display: inline-block; margin: 0 10px;"><svg style="width: 24px; opacity: 0.8;" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 450 512"><path d="M279.1 288l14.2-92.7h-88.9v-60.1c0-25.4 12.4-50.1 52.2-50.1h40.4V6.3S260.4 0 225.4 0c-73.2 0-121.1 44.4-121.1 124.7v70.6H22.9V288h81.4v224h100.2V288z"/></svg></a>
                        <a href="https://www.linkedin.com/company/fpt-telecom-hcm" style="display: inline-block; margin: 0 10px;"><svg style="width: 24px; opacity: 0.8;" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 450 512"><path d="M100.3 448H7.4V148.9h92.9zM53.8 108.1C24.1 108.1 0 83.5 0 53.8a53.8 53.8 0 0 1 107.6 0c0 29.7-24.1 54.3-53.8 54.3zM447.9 448h-92.7V302.4c0-34.7-.7-79.2-48.3-79.2-48.3 0-55.7 37.7-55.7 76.7V448h-92.8V148.9h89.1v40.8h1.3c12.4-23.5 42.7-48.3 87.9-48.3 94 0 111.3 61.9 111.3 142.3V448z"/></svg></a>
                    </div>
                </div>
            </div>
        </body>
        </html>"""

		msg.attach(MIMEText(html_content, 'html'))
		msg.attach(attachment)

		# Send the email
		try:
			s = smtplib.SMTP('smtp.gmail.com', 587)
			s.starttls()
			s.login(self.smtp_username, self.smtp_password)
			s.sendmail(self.smtp_username, email, msg.as_string())
			s.quit()
		except Exception as e:
			print(f'Error sending email: {str(e)}')

		return pdf_url

	def send_group_invitation_email(
		self,
		recipient_email: str,
		group_name: str,
		inviter_name: str,
		invitation_link: str,
		is_new_user: bool,
	):
		"""Send group invitation email.

		Args:
		    recipient_email (str): Email address of the invitee.
		    group_name (str): Name of the group.
		    inviter_name (str): Name of the person who invited the user.
		    invitation_link (str): URL for the user to accept/register.
		    is_new_user (bool): True if the invitee does not have an account yet.
		"""
		msg = MIMEMultipart()
		msg['From'] = self.smtp_username
		msg['To'] = recipient_email

		msg['Subject'] = Header(
			f'{self.project_name} - {_("group_invitation_subject").format(group_name=group_name)}',
			'utf-8',
		)

		if is_new_user:
			body_greeting = _('group_invitation_greeting_new_user')
			body_main_text = _('group_invitation_body_new_user').format(
				inviter_name=inviter_name,
				group_name=group_name,
				project_name=self.project_name,
			)
			button_text = _('group_invitation_button_register_join')
		else:
			body_greeting = _('group_invitation_greeting_existing_user').format(user_name=recipient_email)
			body_main_text = _('group_invitation_body_existing_user').format(
				inviter_name=inviter_name,
				group_name=group_name,
				project_name=self.project_name,
			)
			button_text = _('group_invitation_button_view_invitation')

		body = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; margin: 0; padding: 0; background-color: #f4f4f7; }}
                .email-wrapper {{ width: 100%; padding: 20px 0; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }}
                .header {{ background-color: #4A6FFF; color: white; padding: 20px; text-align: center; }}
                .header h2 {{ margin: 0; font-size: 24px; }}
                .content {{ padding: 30px; color: #51545E; }}
                .content p {{ margin: 16px 0; }}
                .button-container {{ text-align: center; margin: 30px 0; }}
                .button {{ background-color: #4A6FFF; color: white; padding: 12px 25px; text-decoration: none; border-radius: 5px; font-size: 16px; display: inline-block; }}
                .footer {{ font-size: 12px; text-align: center; margin-top: 20px; padding: 20px; color: #777; }}
            </style>
        </head>
        <body>
            <div class="email-wrapper">
                <div class="container">
                    <div class="header">
                        <h2>{self.project_name}</h2>
                    </div>
                    <div class="content">
                        <p>{body_greeting}</p>
                        <p>{body_main_text}</p>
                        <div class="button-container">
                            <a href="{invitation_link}" class="button">{button_text}</a>
                        </div>
                        <p>{_('invitation_link_alternative').format(invitation_link=invitation_link)}</p>
                        <p>{_('group_invitation_ignore')}</p>
                    </div>
                    <div class="footer">
                        <p>&copy; {self.project_name} - {_('do_not_reply')}</p>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
		msg.attach(MIMEText(body, 'html', 'utf-8'))

		try:
			with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
				server.starttls()
				server.login(self.smtp_username, self.smtp_password)
				server.sendmail(self.smtp_username, recipient_email, msg.as_string())
			print(f"Group invitation email sent to {recipient_email} for group '{group_name}'. New user: {is_new_user}")
		except Exception as e:
			print(f'Error sending group invitation email to {recipient_email}: {e}')
