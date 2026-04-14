from sqlalchemy import Column, Integer, String, Float, DateTime, Text
from sqlalchemy.sql import func
from api.database import Base


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    company = Column(String, nullable=False)
    role = Column(String, nullable=False)
    status = Column(String, default="applied")
    notes = Column(Text, default="")
    url = Column(String, default="")
    location = Column(String, default="")
    match_score = Column(Float, default=0)
    match_reason = Column(Text, default="")
    matching_skills = Column(Text, default="")
    missing_skills = Column(Text, default="")
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, onupdate=func.now())


class JobListing(Base):
    __tablename__ = "job_listings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    company = Column(String, nullable=False)
    location = Column(String, default="")
    description = Column(Text, default="")
    url = Column(String, default="")
    source = Column(String, default="")
    date_posted = Column(String, default="")
    days_old = Column(Integer, default=0)
    match_score = Column(Float, default=0)
    match_verdict = Column(String, default="")
    match_reason = Column(Text, default="")
    matching_skills = Column(Text, default="")
    missing_skills = Column(Text, default="")
    created_at = Column(DateTime, server_default=func.now())
