"""
notifications.py - WhatsApp & SMS notification service for DigiLib
Uses Twilio (WhatsApp + SMS) and Fast2SMS (India SMS fallback)

Setup:
  1. Twilio  → https://www.twilio.com  (free trial gives $15 credit)
  2. Fast2SMS→ https://www.fast2sms.com (India, very cheap, Rs.10 = 500 SMS)

Set these environment variables:
  TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_PHONE, TWILIO_WHATSAPP
  FAST2SMS_API_KEY
"""

import requests
from flask import current_app
from datetime import datetime
from models import db, NotificationLog


# ─────────────────────────────────────────────
# MESSAGE TEMPLATES
# ─────────────────────────────────────────────

def msg_registration(student, payment, bookings):
    shifts_info = ', '.join([f"{b.shift.name} (Seat {b.seat.seat_number})" for b in bookings])
    return (
        f"*SHIVA INFOTECH DIGITAL LIBRARY - Registration Confirmed!*\n\n"
        f"Hello *{student.name}*,\n"
        f"Your seat has been booked successfully.\n\n"
        f"*Receipt:* {payment.receipt_number}\n"
        f"*Booking:* {shifts_info}\n"
        f"*Fee:* Rs.{payment.final_amount:.0f}"
        + (f" (Discount: {payment.discount_display()})" if payment.discount_amount > 0 else "") + "\n"
        f"*Payment Mode:* {payment.payment_mode}\n"
        f"*Status:* {payment.status}\n"
        f"*Next Renewal:* {payment.next_due_date.strftime('%d %b %Y') if payment.next_due_date else 'N/A'}\n\n"
        f"Library Hours: 6:00 AM - 9:00 PM\n"
        f"Thank you for choosing SHIVA INFOTECH DIGITAL LIBRARY!"
    )


def msg_payment_confirmed(student, payment):
    return (
        f"*SHIVA INFOTECH DIGITAL LIBRARY - Payment Received!*\n\n"
        f"Hello *{student.name}*,\n"
        f"Your payment of *Rs.{payment.final_amount:.0f}* has been confirmed.\n\n"
        f"*Receipt:* {payment.receipt_number}\n"
        f"*Mode:* {payment.payment_mode}\n"
        f"*Date:* {datetime.now().strftime('%d %b %Y, %I:%M %p')}\n"
        f"*Next Renewal Due:* {payment.next_due_date.strftime('%d %b %Y') if payment.next_due_date else 'N/A'}\n\n"
        f"Thank you! - SHIVA INFOTECH DIGITAL LIBRARY Team"
    )


def msg_fee_reminder(student, reminder):
    overdue = reminder.is_overdue()
    status_text = "OVERDUE" if overdue else "DUE SOON"
    urgency = "Please pay immediately to keep your seat!" if overdue else f"Please pay before {reminder.due_date.strftime('%d %b %Y')}."
    return (
        f"*SHIVA INFOTECH DIGITAL LIBRARY - Fee Reminder* {'⚠️' if overdue else '🔔'}\n\n"
        f"Hello *{student.name}*,\n"
        f"Your monthly library fee is *{status_text}*.\n\n"
        f"*Amount Due:* Rs.{student.base_fee()}\n"
        f"*Due Date:* {reminder.due_date.strftime('%d %b %Y')}\n"
        f"*Month:* {reminder.month_number}\n\n"
        f"{urgency}\n\n"
        f"Contact library to pay.\n"
        f"- SHIVA INFOTECH DIGITAL LIBRARY Team"
    )


def msg_renewal_collected(student, reminder):
    return (
        f"*SHIVA INFOTECH DIGITAL LIBRARY - Renewal Confirmed!*\n\n"
        f"Hello *{student.name}*,\n"
        f"Monthly renewal for *Month {reminder.month_number}* received.\n\n"
        f"*Amount Paid:* Rs.{reminder.final_renewal_amount:.0f}"
        + (f" (Discount: Rs.{reminder.discount_applied:.0f})" if reminder.discount_applied > 0 else "") + "\n"
        f"*Mode:* {reminder.payment_mode}\n"
        f"*Date:* {datetime.now().strftime('%d %b %Y')}\n\n"
        f"See you at the library! - SHIVA INFOTECH DIGITAL LIBRARY Team"
    )


# ─────────────────────────────────────────────
# TWILIO SENDER
# ─────────────────────────────────────────────

def send_via_twilio_whatsapp(to_number, message, student_id, msg_type):
    """Send WhatsApp message via Twilio"""
    sid   = current_app.config.get('TWILIO_ACCOUNT_SID')
    token = current_app.config.get('TWILIO_AUTH_TOKEN')
    from_ = current_app.config.get('TWILIO_WHATSAPP')

    if not all([sid, token, from_]):
        _log(student_id, 'whatsapp', msg_type, to_number, message, 'skipped', 'Twilio not configured')
        return False, 'Twilio WhatsApp not configured'

    try:
        from twilio.rest import Client
        client = Client(sid, token)
        msg = client.messages.create(
            body=message,
            from_=from_,
            to=f"whatsapp:+91{to_number}"
        )
        _log(student_id, 'whatsapp', msg_type, to_number, message, 'sent')
        return True, msg.sid
    except Exception as e:
        _log(student_id, 'whatsapp', msg_type, to_number, message, 'failed', str(e))
        return False, str(e)


def send_via_twilio_sms(to_number, message, student_id, msg_type):
    """Send SMS via Twilio"""
    sid   = current_app.config.get('TWILIO_ACCOUNT_SID')
    token = current_app.config.get('TWILIO_AUTH_TOKEN')
    from_ = current_app.config.get('TWILIO_PHONE')

    if not all([sid, token, from_]):
        _log(student_id, 'sms', msg_type, to_number, message, 'skipped', 'Twilio SMS not configured')
        return False, 'Twilio SMS not configured'

    try:
        from twilio.rest import Client
        client = Client(sid, token)
        msg = client.messages.create(
            body=message,
            from_=from_,
            to=f"+91{to_number}"
        )
        _log(student_id, 'sms', msg_type, to_number, message, 'sent')
        return True, msg.sid
    except Exception as e:
        _log(student_id, 'sms', msg_type, to_number, message, 'failed', str(e))
        return False, str(e)


def send_via_fast2sms(to_number, message, student_id, msg_type):
    """Send SMS via Fast2SMS (India - cheap alternative)"""
    api_key = current_app.config.get('FAST2SMS_API_KEY')
    if not api_key:
        _log(student_id, 'sms', msg_type, to_number, message, 'skipped', 'Fast2SMS not configured')
        return False, 'Fast2SMS not configured'

    try:
        # Strip WhatsApp formatting (*bold* etc) for plain SMS
        plain_msg = message.replace('*', '').replace('\n\n', '\n')
        response = requests.post(
            'https://www.fast2sms.com/dev/bulkV2',
            headers={'authorization': api_key},
            data={
                'route': 'q',
                'message': plain_msg,
                'language': 'english',
                'flash': 0,
                'numbers': to_number,
            },
            timeout=10
        )
        data = response.json()
        if data.get('return'):
            _log(student_id, 'sms', msg_type, to_number, plain_msg, 'sent')
            return True, data.get('request_id', 'ok')
        else:
            err = str(data)
            _log(student_id, 'sms', msg_type, to_number, plain_msg, 'failed', err)
            return False, err
    except Exception as e:
        _log(student_id, 'sms', msg_type, to_number, message, 'failed', str(e))
        return False, str(e)


# ─────────────────────────────────────────────
# MAIN DISPATCHER
# ─────────────────────────────────────────────

def notify(student, message, msg_type, channels=('whatsapp', 'sms')):
    """
    Send notification to a student via configured channels.
    Returns dict with results per channel.
    Silently skips if services not configured (won't break the app).
    """
    results = {}
    mobile  = student.mobile

    if 'whatsapp' in channels:
        ok, info = send_via_twilio_whatsapp(mobile, message, student.id, msg_type)
        results['whatsapp'] = {'ok': ok, 'info': info}

    if 'sms' in channels:
        # Try Fast2SMS first (cheaper for India), fall back to Twilio SMS
        f2s_key = current_app.config.get('FAST2SMS_API_KEY')
        if f2s_key:
            ok, info = send_via_fast2sms(mobile, message, student.id, msg_type)
        else:
            ok, info = send_via_twilio_sms(mobile, message, student.id, msg_type)
        results['sms'] = {'ok': ok, 'info': info}

    return results


# ─────────────────────────────────────────────
# CONVENIENCE FUNCTIONS
# ─────────────────────────────────────────────

def notify_registration(student, payment, bookings):
    msg = msg_registration(student, payment, bookings)
    return notify(student, msg, 'registration')


def notify_payment_confirmed(student, payment):
    msg = msg_payment_confirmed(student, payment)
    return notify(student, msg, 'payment_confirmed')


def notify_fee_reminder(student, reminder):
    msg = msg_fee_reminder(student, reminder)
    results = notify(student, msg, 'fee_reminder')
    # Mark as sent in DB
    if results.get('whatsapp', {}).get('ok'):
        reminder.whatsapp_sent = True
    if results.get('sms', {}).get('ok'):
        reminder.sms_sent = True
    reminder.sent_at = datetime.utcnow()
    db.session.commit()
    return results


def notify_renewal_collected(student, reminder):
    msg = msg_renewal_collected(student, reminder)
    return notify(student, msg, 'renewal_collected')


def send_bulk_reminders():
    """
    Send WhatsApp/SMS reminders for all pending/overdue fee reminders.
    Call this from admin panel or scheduled job.
    """
    from models import FeeReminder
    from datetime import date, timedelta
    today     = date.today()
    days_before = current_app.config.get('REMINDER_DAYS_BEFORE', 3)
    threshold = today + timedelta(days=days_before)

    # Get all pending reminders due within threshold
    pending = FeeReminder.query.filter(
        FeeReminder.status.in_(['Pending', 'Overdue']),
        FeeReminder.due_date <= threshold,
        FeeReminder.whatsapp_sent == False
    ).all()

    sent_count = 0
    for reminder in pending:
        results = notify_fee_reminder(reminder.student, reminder)
        if any(r.get('ok') for r in results.values()):
            sent_count += 1

    return sent_count


# ─────────────────────────────────────────────
# INTERNAL LOGGER
# ─────────────────────────────────────────────

def _log(student_id, channel, msg_type, mobile, body, status, error=None):
    try:
        log = NotificationLog(
            student_id    = student_id,
            channel       = channel,
            message_type  = msg_type,
            mobile        = mobile,
            message_body  = body[:1000],
            status        = status,
            error_message = error
        )
        db.session.add(log)
        db.session.commit()
    except Exception:
        pass  # Never let logging break the main flow
