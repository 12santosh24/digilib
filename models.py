"""
models.py - SQLAlchemy ORM models for DigiLib
"""
from datetime import datetime, date
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class Admin(UserMixin, db.Model):
    __tablename__ = 'admins'
    id            = db.Column(db.Integer, primary_key=True)
    username      = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, pw):   self.password_hash = generate_password_hash(pw)
    def check_password(self, pw): return check_password_hash(self.password_hash, pw)


class Shift(db.Model):
    __tablename__ = 'shifts'
    id           = db.Column(db.Integer, primary_key=True)
    shift_number = db.Column(db.Integer, nullable=False, unique=True)
    name         = db.Column(db.String(50), nullable=False)
    start_time   = db.Column(db.String(20), nullable=False)
    end_time     = db.Column(db.String(20), nullable=False)
    bookings     = db.relationship('Booking', backref='shift', lazy=True)


class Seat(db.Model):
    __tablename__ = 'seats'
    id          = db.Column(db.Integer, primary_key=True)
    seat_number = db.Column(db.Integer, nullable=False, unique=True)
    bookings    = db.relationship('Booking', backref='seat', lazy=True)

    def is_booked_for_shift(self, shift_id):
        return Booking.query.filter_by(seat_id=self.id, shift_id=shift_id, is_active=True).first() is not None


class Student(db.Model):
    __tablename__  = 'students'
    id             = db.Column(db.Integer, primary_key=True)
    name           = db.Column(db.String(100), nullable=False)
    mobile         = db.Column(db.String(10), unique=True, nullable=False)
    dob            = db.Column(db.Date, nullable=False)
    num_shifts     = db.Column(db.Integer, nullable=False)
    registered_at  = db.Column(db.DateTime, default=datetime.utcnow)

    bookings      = db.relationship('Booking',     backref='student', lazy=True, cascade='all, delete-orphan')
    payment       = db.relationship('Payment',     backref='student', uselist=False, cascade='all, delete-orphan')
    fee_reminders = db.relationship('FeeReminder', backref='student', lazy=True, cascade='all, delete-orphan')

    def base_fee(self):
        return {1: 300, 2: 500, 3: 700}.get(self.num_shifts, 0)

    def total_fee(self):
        return self.payment.final_amount if self.payment else self.base_fee()

    def months_active(self):
        today = date.today()
        reg   = self.registered_at.date()
        return (today.year - reg.year) * 12 + (today.month - reg.month)

    def whatsapp_number(self):
        """Format mobile for WhatsApp (Indian numbers)"""
        return f"whatsapp:+91{self.mobile}"

    def sms_number(self):
        return f"+91{self.mobile}"


class Booking(db.Model):
    __tablename__ = 'bookings'
    id         = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    seat_id    = db.Column(db.Integer, db.ForeignKey('seats.id'),    nullable=False)
    shift_id   = db.Column(db.Integer, db.ForeignKey('shifts.id'),   nullable=False)
    booked_at  = db.Column(db.DateTime, default=datetime.utcnow)
    is_active  = db.Column(db.Boolean, default=True)

    __table_args__ = (
        db.UniqueConstraint('seat_id', 'shift_id', 'is_active', name='uq_seat_shift_active'),
    )


class Payment(db.Model):
    __tablename__    = 'payments'
    id               = db.Column(db.Integer, primary_key=True)
    student_id       = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False, unique=True)
    receipt_number   = db.Column(db.String(20), unique=True, nullable=False)

    original_amount  = db.Column(db.Float, nullable=False)
    discount_type    = db.Column(db.String(20), default='none')   # none / percent / flat
    discount_value   = db.Column(db.Float, default=0.0)
    discount_reason  = db.Column(db.String(100), default='')
    discount_amount  = db.Column(db.Float, default=0.0)
    final_amount     = db.Column(db.Float, nullable=False)

    status           = db.Column(db.String(10), default='Unpaid')  # Paid / Unpaid
    payment_mode     = db.Column(db.String(10), default='Offline') # Online / Offline
    transaction_id   = db.Column(db.String(50), nullable=True)
    payment_date     = db.Column(db.DateTime, nullable=True)

    renewal_month    = db.Column(db.Integer, default=1)
    next_due_date    = db.Column(db.Date, nullable=True)
    created_at       = db.Column(db.DateTime, default=datetime.utcnow)

    def discount_display(self):
        if self.discount_type == 'percent': return f"{int(self.discount_value)}% off"
        if self.discount_type == 'flat':    return f"Rs.{int(self.discount_value)} flat"
        return "None"


class FeeReminder(db.Model):
    __tablename__         = 'fee_reminders'
    id                    = db.Column(db.Integer, primary_key=True)
    student_id            = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    month_number          = db.Column(db.Integer, nullable=False)
    due_date              = db.Column(db.Date, nullable=False)
    renewal_amount        = db.Column(db.Float, nullable=True)
    discount_applied      = db.Column(db.Float, default=0.0)
    final_renewal_amount  = db.Column(db.Float, nullable=True)
    payment_mode          = db.Column(db.String(10), nullable=True)
    transaction_id        = db.Column(db.String(50), nullable=True)
    paid_at               = db.Column(db.DateTime, nullable=True)
    status                = db.Column(db.String(10), default='Pending')  # Pending/Paid/Overdue
    # Notification tracking
    whatsapp_sent         = db.Column(db.Boolean, default=False)
    sms_sent              = db.Column(db.Boolean, default=False)
    sent_at               = db.Column(db.DateTime, nullable=True)
    created_at            = db.Column(db.DateTime, default=datetime.utcnow)

    def is_overdue(self):
        return self.status == 'Pending' and self.due_date < date.today()


class NotificationLog(db.Model):
    """Log every WhatsApp/SMS notification sent"""
    __tablename__   = 'notification_logs'
    id              = db.Column(db.Integer, primary_key=True)
    student_id      = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    channel         = db.Column(db.String(20), nullable=False)   # 'whatsapp' or 'sms'
    message_type    = db.Column(db.String(30), nullable=False)   # 'registration' / 'reminder' / 'paid'
    mobile          = db.Column(db.String(15), nullable=False)
    message_body    = db.Column(db.Text, nullable=False)
    status          = db.Column(db.String(20), default='sent')   # sent / failed
    error_message   = db.Column(db.Text, nullable=True)
    sent_at         = db.Column(db.DateTime, default=datetime.utcnow)
    student         = db.relationship('Student', backref='notifications', lazy=True)
