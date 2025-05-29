from sqlalchemy import Column, String, Float, Integer, Text, JSON, Enum
from sqlalchemy.orm import relationship
from app.core.base_model import BaseEntity
import enum


class ModelProvider(str, enum.Enum):
    """Model provider enumeration"""
    OPENAI = 'openai'
    ANTHROPIC = 'anthropic'
    GOOGLE = 'google'
    GROQ = 'groq'
    OLLAMA = 'ollama'


class AgentConfig(BaseEntity):
    """Agent configuration model - stores LLM and workflow settings"""
    
    __tablename__ = 'agent_configs'
    
    name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    agent_type = Column(String(50), nullable=False)
    model_provider = Column(Enum(ModelProvider), nullable=False, default=ModelProvider.OPENAI)
    model_name = Column(String(100), nullable=False)
    temperature = Column(Float, nullable=False, default=0.7)
    max_tokens = Column(Integer, nullable=True, default=2048)
    system_prompt = Column(Text, nullable=True)
    tools_config = Column(JSON, nullable=True)  # JSON config for tools
    workflow_config = Column(JSON, nullable=True)  # JSON config for LangGraph workflow
    memory_config = Column(JSON, nullable=True)  # JSON config for memory settings
    
    # Relationships
    agents = relationship('Agent', back_populates='config')
    
    def __repr__(self):
        return f"<AgentConfig(id={self.id}, name={self.name}, provider={self.model_provider})>"