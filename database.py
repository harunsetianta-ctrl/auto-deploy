from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import DATABASE_URL

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True)
    username = Column(String)
    phone = Column(String)
    string_session = Column(String)
    is_premium = Column(Boolean, default=False)
    premium_until = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class Transaction(Base):
    __tablename__ = "transactions"
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer)
    package = Column(String)
    amount = Column(Integer)
    status = Column(String, default="pending")  # pending, paid, deployed
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(engine)

def get_user(telegram_id):
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    db.close()
    return user

def create_user(telegram_id, username):
    db = SessionLocal()
    user = User(telegram_id=telegram_id, username=username)
    db.add(user)
    db.commit()
    db.close()
    return user

def update_user_session(telegram_id, phone, string_session):
    db = SessionLocal()
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if user:
        user.phone = phone
        user.string_session = string_session
        user.is_premium = True
        db.commit()
    db.close()

def create_transaction(telegram_id, package, amount):
    db = SessionLocal()
    trans = Transaction(telegram_id=telegram_id, package=package, amount=amount)
    db.add(trans)
    db.commit()
    db.close()
    return trans