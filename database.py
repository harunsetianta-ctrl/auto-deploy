from sqlalchemy import create_engine, Column, Integer, BigInteger, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime, timedelta
from config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True)
    username = Column(String)
    phone = Column(String)
    string_session = Column(String)
    is_premium = Column(Boolean, default=False)
    premium_until = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger)
    order_id = Column(String, unique=True)
    invoice_id = Column(String)
    package = Column(String)
    amount = Column(Integer)
    status = Column(String, default="pending")  # pending, paid, expired, deployed
    payment_url = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    paid_at = Column(DateTime)


Base.metadata.create_all(engine)


def get_user(telegram_id):
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    db.close()
    return user


def create_user(telegram_id, username):
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id, username=username)
        db.add(user)
        db.commit()
        db.refresh(user)
    db.close()
    return user


def update_user_session(telegram_id, phone, string_session):
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if user:
        user.phone = phone
        user.string_session = string_session
        db.commit()
    db.close()


def grant_premium(telegram_id, days=None):
    """days=None berarti lifetime (premium_until dibiarkan kosong)."""
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if user:
        user.is_premium = True
        user.premium_until = (
            datetime.utcnow() + timedelta(days=days) if days else None
        )
        db.commit()
    db.close()


def create_transaction(telegram_id, order_id, package, amount):
    db = SessionLocal()
    trans = Transaction(
        telegram_id=telegram_id,
        order_id=order_id,
        package=package,
        amount=amount,
    )
    db.add(trans)
    db.commit()
    db.refresh(trans)
    db.close()
    return trans


def set_transaction_invoice(order_id, invoice_id, payment_url):
    db = SessionLocal()
    trans = db.query(Transaction).filter(Transaction.order_id == order_id).first()
    if trans:
        trans.invoice_id = invoice_id
        trans.payment_url = payment_url
        db.commit()
    db.close()


def get_transaction_by_order_id(order_id):
    db = SessionLocal()
    trans = db.query(Transaction).filter(Transaction.order_id == order_id).first()
    db.close()
    return trans


def mark_transaction_paid(order_id):
    db = SessionLocal()
    trans = db.query(Transaction).filter(Transaction.order_id == order_id).first()
    if trans and trans.status == "pending":
        trans.status = "paid"
        trans.paid_at = datetime.utcnow()
        db.commit()
    db.close()
    return trans


def mark_transaction_expired(order_id):
    db = SessionLocal()
    trans = db.query(Transaction).filter(Transaction.order_id == order_id).first()
    if trans and trans.status == "pending":
        trans.status = "expired"
        db.commit()
    db.close()
