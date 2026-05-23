import logging
from flask import current_app
from flask_mail import Message
from app.database.models import db, Notification

logger = logging.getLogger(__name__)

class NotificationService:
    @staticmethod
    def send_notification(user, title, message, type='info', icon='🔔', action='View', buy_url=None):
        """
        Dispatches notification:
        1. In-app notification saved to Database.
        2. Email notification via Flask-Mail (if keys exist).
        """
        # 1. Save in-app notification
        try:
            notif = Notification(
                user_id=user.id,
                type=type,
                icon=icon,
                title=title,
                message=message,
                action=action,
                buy_url=buy_url
            )
            db.session.add(notif)
            db.session.commit()
            logger.info(f"In-app notification created for user {user.id}: {title}")
        except Exception as e:
            db.session.rollback()
            logger.error(f"Failed to create in-app notification: {e}")

        # 2. Email notification (Flask-Mail)
        try:
            from app import mail  # Avoid circular import
            
            # Check if SMTP configuration is set up
            if not current_app.config.get('MAIL_USERNAME'):
                logger.info("SMTP configuration not provided. Skipping email dispatch.")
                return

            msg = Message(
                subject=f"PriceAI Alert: {title}",
                recipients=[user.email],
                body=f"Hello {user.name or 'User'},\n\n{message}\n\nLink: {buy_url or 'http://localhost:5000'}\n\nBest,\nPriceAI Team"
            )
            
            # Send email
            mail.send(msg)
            logger.info(f"Email notification successfully sent to {user.email}")
            
        except Exception as e:
            logger.error(f"Failed to send email notification: {e}")

    @staticmethod
    def send_system_log(title, message):
        """Log placeholder for future WhatsApp/Telegram channels"""
        logger.info(f"[Notification Channel Log] {title} - {message}")
