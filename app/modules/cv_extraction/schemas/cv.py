from typing import Optional, List, Dict, Any, Union
from pydantic import BaseModel, Field
from app.core.base_model import RequestSchema


class ProcessCVRequest(RequestSchema):
    cv_file_url: Optional[str] = None


class PersonalInformation(BaseModel):
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone_number: Optional[str] = None
    linkedin_url: Optional[str] = None
    github_url: Optional[str] = None
    portfolio_url: Optional[str] = None
    other_url: Optional[List[str]] = None
    address: Optional[str] = None


class EducationItem(BaseModel):
    institution_name: Optional[str] = None
    degree_name: Optional[str] = None
    major: Optional[str] = None
    graduation_date: Optional[str] = None
    gpa: Optional[Union[str, float]] = None
    relevant_courses: Optional[List[str]] = None
    description: Optional[str] = None


class EducationHistory(BaseModel):
    items: List[EducationItem] = Field(default_factory=list)


class WorkExperienceItem(BaseModel):
    company_name: Optional[str] = None
    job_title: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    duration: Optional[str] = None
    responsibilities_achievements: Optional[List[str]] = None
    location: Optional[str] = None


class WorkExperienceHistory(BaseModel):
    items: List[WorkExperienceItem] = Field(default_factory=list)


class SkillItem(BaseModel):
    skill_name: Optional[str] = None
    proficiency_level: Optional[Union[str, float]] = None
    category: Optional[str] = None


class SkillsSummary(BaseModel):
    items: List[SkillItem] = Field(default_factory=list)


class ProjectItem(BaseModel):
    project_name: Optional[str] = None
    description: Optional[str] = None
    technologies_used: Optional[List[str]] = None
    role: Optional[str] = None
    project_url: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class ProjectsShowcase(BaseModel):
    items: List[ProjectItem] = Field(default_factory=list)


class CertificateItem(BaseModel):
    certificate_name: Optional[str] = None
    issuing_organization: Optional[str] = None
    issue_date: Optional[str] = None
    expiration_date: Optional[str] = None
    credential_id: Optional[str] = None


class CertificatesAndCourses(BaseModel):
    items: List[CertificateItem] = Field(default_factory=list)


class KeywordItem(BaseModel):
    keyword: str


class ExtractedKeywords(BaseModel):
    items: List[KeywordItem] = Field(default_factory=list)


class CharacteristicItem(BaseModel):
    characteristic_type: Optional[str] = None
    statement: Optional[str] = None
    evidence: Optional[List[str]] = None


class InferredCharacteristics(BaseModel):
    items: List[CharacteristicItem] = Field(default_factory=list)


class LLMTokenUsage(BaseModel):
    input_tokens: Optional[int] = None
    output_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    price_usd: Optional[float] = None


class CVAnalysisResult(BaseModel):
    identified_sections: Optional[List[str]] = None
    personal_information: Optional[PersonalInformation] = None
    education_history: Optional[EducationHistory] = None
    work_experience_history: Optional[WorkExperienceHistory] = None
    projects: Optional[ProjectsShowcase] = None
    certificates_and_courses: Optional[CertificatesAndCourses] = None
    interests_and_hobbies: Optional[Any] = None
    skills_summary: Optional[SkillsSummary] = None
    other_sections_data: Optional[Dict[str, Any]] = None
    inferred_characteristics: Optional[List[CharacteristicItem]] = None
    keywords: Optional[List[str]] = None
    cv_summary: Optional[str] = None
    extracted_keywords: Optional[ExtractedKeywords] = None
    llm_token_usage: Optional[LLMTokenUsage] = None


class ProcessCVResponse(BaseModel):
    filename: Optional[str] = None
    file_path: Optional[str] = None
    cv_file_url: Optional[str] = None
    extracted_text: Optional[str] = None
    cv_analysis_result: Optional[CVAnalysisResult] = None
    personal_info: Optional[PersonalInformation] = None
    skills_count: Optional[int] = None
    experience_count: Optional[int] = None
    cv_summary: Optional[str] = None
