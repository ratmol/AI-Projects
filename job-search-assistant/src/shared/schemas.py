"""Data schemas using Pydantic."""
from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, field_validator


class ExperienceLevel(BaseModel):
    years: Optional[str] = None
    seniority: Optional[str] = None


class SalaryRange(BaseModel):
    min: Optional[float] = None
    max: Optional[float] = None
    currency: Optional[str] = None


class CompanyResearch(BaseModel):
    size: Optional[str] = None
    industry: Optional[str] = None
    recentNews: Optional[str] = None
    cultureNotes: Optional[str] = None


class JobPosting(BaseModel):
    jobTitle: Optional[str] = "not listed"
    companyName: Optional[str] = "not listed"
    location: Optional[str] = "not listed"
    remoteStatus: str = "not listed"
    requiredSkills: list[str] = []
    preferredSkills: list[str] = []
    experienceLevel: ExperienceLevel = ExperienceLevel()
    educationRequired: Optional[str] = None
    salaryRange: SalaryRange = SalaryRange()
    responsibilities: list[str] = []
    companyResearch: CompanyResearch = CompanyResearch()

    @field_validator("remoteStatus")
    @classmethod
    def validate_remote_status(cls, v):
        allowed = {"remote", "hybrid", "on-site", "not listed"}
        return v if v in allowed else "not listed"

    class Config:
        populate_by_name = True


class WorkExperience(BaseModel):
    role: str = "unknown"
    company: str = "unknown"
    durationMonths: Optional[int] = None
    responsibilities: list[str] = []


class Education(BaseModel):
    degree: str = "unknown"
    institution: str = "unknown"
    year: Optional[str] = None


class Project(BaseModel):
    name: str = "unknown"
    description: str = ""
    technologies: list[str] = []


class Resume(BaseModel):
    hardSkills: list[str] = []
    softSkills: list[str] = []
    workExperience: list[WorkExperience] = []
    education: list[Education] = []
    certifications: list[str] = []
    projects: list[Project] = []
    keywords: list[str] = []
