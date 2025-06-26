'use client'

import React from 'react'
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome'
import { 
  faUser, 
  faEnvelope, 
  faPhone, 
  faGraduationCap, 
  faBriefcase, 
  faCog, 
  faCertificate,
  faTimes,
  faMapMarkerAlt,
  faGlobe,
  faChartBar,
  faClock,
  faLightbulb,
  faProjectDiagram,
  faHashtag,
  faRobot,
  faCheckCircle,
  faInfoCircle
} from '@fortawesome/free-solid-svg-icons'
import { 
  faGithub,
  faLinkedin
} from '@fortawesome/free-brands-svg-icons'
import { useTranslation } from '@/contexts/TranslationContext'
import { Button } from '@/components/ui/button'
import ScrollReveal from '@/components/animations/ScrollReveal'

interface CVAnalysisResult {
  file_path: string
  cv_file_url: string
  extracted_text: string
  cv_analysis_result: {
    identified_sections?: string[]
    personal_information?: {
      full_name?: string
      email?: string
      phone_number?: string
      linkedin_url?: string
      github_url?: string
      portfolio_url?: string
      other_url?: string[]
      address?: string
    }
    education_history?: {
      items: Array<{
        institution_name?: string
        degree_name?: string
        major?: string
        graduation_date?: string
        gpa?: string | number
        relevant_courses?: string[]
        description?: string
      }>
    }
    work_experience_history?: {
      items: Array<{
        company_name?: string
        job_title?: string
        start_date?: string
        end_date?: string
        duration?: string
        responsibilities_achievements?: string[]
        location?: string
      }>
    }
    skills_summary?: {
      items: Array<{
        skill_name?: string
        proficiency_level?: string | number
        category?: string
      }>
    }
    projects?: {
      items: Array<{
        project_name?: string
        description?: string
        technologies_used?: string[]
        role?: string
        project_url?: string
        start_date?: string
        end_date?: string
      }>
    }
    certificates_and_courses?: {
      items: Array<{
        certificate_name?: string
        issuing_organization?: string
        issue_date?: string
        expiration_date?: string
        credential_id?: string
      }>
    }
    extracted_keywords?: {
      items: Array<{ keyword: string }>
    }
    keywords?: string[]
    inferred_characteristics?: Array<{
      characteristic_type?: string
      statement?: string
      evidence?: string[]
    }>
    llm_token_usage?: {
      input_tokens?: number
      output_tokens?: number
      total_tokens?: number
      price_usd?: number
    }
    cv_summary?: string
  }
  personal_info: {
    full_name?: string
    email?: string
    phone_number?: string
    linkedin_url?: string
    github_url?: string
    portfolio_url?: string
    other_url?: string[]
    address?: string
  }
  skills_count: number
  experience_count: number
  cv_summary: string
}

interface CVModalProps {
  isVisible: boolean
  onClose: () => void
  cvData: CVAnalysisResult | null
}

export function CVModal({ isVisible, onClose, cvData }: CVModalProps) {
  const { t } = useTranslation()

  if (!isVisible || !cvData) return null

  const {
    cv_summary,
    skills_count,
    experience_count,
    cv_analysis_result
  } = cvData
  const analysis = cv_analysis_result
  const personalInfo = analysis?.personal_information
  const skills = analysis?.skills_summary?.items || []
  const experiences = analysis?.work_experience_history?.items || []
  const education = analysis?.education_history?.items || []
  const certificates = analysis?.certificates_and_courses?.items || []
  const projects = analysis?.projects?.items || []
  const keywords = analysis?.extracted_keywords?.items || analysis?.keywords || []
  const characteristics = analysis?.inferred_characteristics || []
  const tokenUsage = analysis?.llm_token_usage

  return (
    <>
      {/* Backdrop */}
      <div 
        className="fixed inset-0 bg-black/50 z-50 backdrop-blur-sm cv-backdrop"
        onClick={onClose}
      />
      
      {/* Modal */}
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 cv-modal-container">
        <div className="bg-[color:var(--card)] rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden border border-[color:var(--border)]">
          {/* Header */}
          <div className="bg-gradient-to-r from-[color:var(--feature-blue)] to-[color:var(--feature-purple)] p-6 text-[color:var(--foreground)] relative">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-2xl font-bold mb-2 animate-slideInLeft text-[color:var(--foreground)]">
                  {personalInfo?.full_name || t('cv.cvAnalysis') || 'CV Analysis'}
                </h2>
                <p className="text-[color:var(--foreground)] animate-slideInLeft animate-delay-100">
                  {personalInfo?.email && (
                    <span className="mr-4">
                      <FontAwesomeIcon icon={faEnvelope} className="mr-2" />
                      {personalInfo.email}
                    </span>
                  )}
                  {personalInfo?.phone_number && (
                    <span>
                      <FontAwesomeIcon icon={faPhone} className="mr-2" />
                      {personalInfo.phone_number}
                    </span>
                  )}
                </p>
              </div>
              <Button
                onClick={onClose}
                variant="ghost"
                size="sm"
                className="text-[color:var(--foreground)] hover:bg-white/20 animate-slideInRight"
              >
                <FontAwesomeIcon icon={faTimes} />
              </Button>
            </div>

            {/* Stats Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-6">
              <div className="bg-white/10 rounded-lg p-3 backdrop-blur-sm animate-scaleIn animate-delay-200">
                <div className="flex items-center">
                  <FontAwesomeIcon icon={faCog} className="text-2xl mr-3" />
                  <div>
                    <div className="text-xl font-bold">{skills_count}</div>
                    <div className="text-sm text-[color:var(--foreground)]">{t('cv.skills')}</div>
                  </div>
                </div>
              </div>
              
              <div className="bg-white/10 rounded-lg p-3 backdrop-blur-sm animate-scaleIn animate-delay-300">
                <div className="flex items-center">
                  <FontAwesomeIcon icon={faBriefcase} className="text-2xl mr-3" />
                  <div>
                    <div className="text-xl font-bold">{experience_count}</div>
                    <div className="text-sm text-[color:var(--foreground)]">{t('cv.experience')}</div>
                  </div>
                </div>
              </div>

              <div className="bg-white/10 rounded-lg p-3 backdrop-blur-sm animate-scaleIn animate-delay-400">
                <div className="flex items-center">
                  <FontAwesomeIcon icon={faGraduationCap} className="text-2xl mr-3" />
                  <div>
                    <div className="text-xl font-bold">{education.length}</div>
                    <div className="text-sm text-[color:var(--foreground)]">{t('cv.education')}</div>
                  </div>
                </div>
              </div>

              <div className="bg-white/10 rounded-lg p-3 backdrop-blur-sm animate-scaleIn animate-delay-500">
                <div className="flex items-center">
                  <FontAwesomeIcon icon={faCertificate} className="text-2xl mr-3" />
                  <div>
                    <div className="text-xl font-bold">{certificates.length}</div>
                    <div className="text-sm text-[color:var(--foreground)]">{t('cv.certificates')}</div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Content */}
          <div className="p-6 overflow-y-auto max-h-[calc(90vh-200px)] scrollbar-thin scrollbar-thumb-[color:var(--muted)] scrollbar-track-transparent">
            <div className="space-y-6">
                        {/* CV Summary */}
          {cv_summary && (
            <ScrollReveal>
              <div className="animate-slideInUp animate-delay-100">
                <h3 className="text-lg font-semibold text-[color:var(--foreground)] mb-3 flex items-center">
                  <FontAwesomeIcon icon={faChartBar} className="mr-2 text-[color:var(--feature-blue-text)]" />
                  {t('cv.summary') || 'Summary'}
                </h3>
                <div className="bg-[color:var(--muted)]/30 rounded-lg p-4 glass-effect">
                  <p className="text-[color:var(--foreground)] leading-relaxed">{cv_summary}</p>
                </div>
              </div>
            </ScrollReveal>
          )}

              {/* Personal Information */}
              {personalInfo && (
                <div className="animate-slideInUp animate-delay-200">
                  <h3 className="text-lg font-semibold text-[color:var(--foreground)] mb-3 flex items-center">
                    <FontAwesomeIcon icon={faUser} className="mr-2 text-[color:var(--feature-green-text)]" />
                    {t('cv.personalInfo') || 'Personal Information'}
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {personalInfo.github_url && (
                      <div className="flex items-center p-3 bg-[color:var(--muted)]/30 rounded-lg glass-effect hover:scale-105 transition-all duration-300">
                        <FontAwesomeIcon icon={faGithub} className="mr-3 text-[color:var(--feature-purple-text)]" />
                        <a 
                          href={`https://${personalInfo.github_url}`} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-[color:var(--feature-blue-text)] hover:underline transition-colors duration-200"
                        >
                          {personalInfo.github_url}
                        </a>
                      </div>
                    )}
                    {personalInfo.linkedin_url && (
                      <div className="flex items-center p-3 bg-[color:var(--muted)]/30 rounded-lg glass-effect hover:scale-105 transition-all duration-300">
                        <FontAwesomeIcon icon={faLinkedin} className="mr-3 text-[color:var(--feature-blue-text)]" />
                        <a 
                          href={`https://${personalInfo.linkedin_url}`} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-[color:var(--feature-blue-text)] hover:underline transition-colors duration-200"
                        >
                          {personalInfo.linkedin_url}
                        </a>
                      </div>
                    )}
                    {personalInfo.portfolio_url && (
                      <div className="flex items-center p-3 bg-[color:var(--muted)]/30 rounded-lg glass-effect hover:scale-105 transition-all duration-300">
                        <FontAwesomeIcon icon={faGlobe} className="mr-3 text-[color:var(--feature-yellow-text)]" />
                        <a 
                          href={personalInfo.portfolio_url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="text-[color:var(--feature-blue-text)] hover:underline transition-colors duration-200"
                        >
                          Portfolio
                        </a>
                      </div>
                    )}
                    {personalInfo.address && (
                      <div className="flex items-center p-3 bg-[color:var(--muted)]/30 rounded-lg glass-effect hover:scale-105 transition-all duration-300">
                        <FontAwesomeIcon icon={faMapMarkerAlt} className="mr-3 text-[color:var(--feature-green-text)]" />
                        <span className="text-[color:var(--foreground)]">{personalInfo.address}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Skills */}
              {skills.length > 0 && (
                <div className="animate-slideInUp animate-delay-300">
                  <h3 className="text-lg font-semibold text-[color:var(--foreground)] mb-3 flex items-center">
                    <FontAwesomeIcon icon={faCog} className="mr-2 text-[color:var(--feature-purple-text)]" />
                    {t('cv.skills') || 'Skills'} ({skills.length})
                  </h3>
                  <div className="flex flex-wrap gap-2">
                    {skills.map((skill, index) => (
                      <span
                        key={index}
                        className="bg-gradient-to-r from-[color:var(--gradient-button-from)] to-[color:var(--gradient-button-to)] text-[color:var(--primary-foreground)] px-3 py-1 rounded-full text-sm font-medium animate-fadeIn hover:scale-105 transition-all duration-200 hover:shadow-lg skill-glow"
                        style={{ animationDelay: `${index * 50}ms` }}
                      >
                        {skill.skill_name}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Work Experience */}
              {experiences.length > 0 && (
                <div className="animate-slideInUp animate-delay-400">
                  <h3 className="text-lg font-semibold text-[color:var(--foreground)] mb-3 flex items-center">
                    <FontAwesomeIcon icon={faBriefcase} className="mr-2 text-[color:var(--feature-green-text)]" />
                    {t('cv.workExperience') || 'Work Experience'}
                  </h3>
                  <div className="space-y-4">
                    {experiences.map((exp, index) => (
                      <div
                        key={index}
                        className="border border-[color:var(--border)] rounded-lg p-4 hover:bg-[color:var(--muted)]/20 transition-all duration-300 animate-slideInLeft glass-effect cv-card-hover"
                        style={{ animationDelay: `${index * 100}ms` }}
                      >
                        <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-2">
                          <h4 className="font-semibold text-[color:var(--foreground)]">
                            {exp.job_title} - {exp.company_name}
                          </h4>
                          <div className="flex items-center text-sm text-[color:var(--muted-foreground)]">
                            <FontAwesomeIcon icon={faClock} className="mr-1" />
                            {exp.start_date} - {exp.end_date}
                          </div>
                        </div>
                        {exp.location && (
                          <div className="flex items-center text-sm text-[color:var(--muted-foreground)] mb-2">
                            <FontAwesomeIcon icon={faMapMarkerAlt} className="mr-1" />
                            {exp.location}
                          </div>
                        )}
                        {exp.responsibilities_achievements && exp.responsibilities_achievements.length > 0 && (
                          <ul className="list-disc list-inside text-sm text-[color:var(--foreground)] space-y-1">
                            {exp.responsibilities_achievements.map((responsibility, idx) => (
                              <li key={idx}>{responsibility}</li>
                            ))}
                          </ul>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Education */}
              {education.length > 0 && (
                <div className="animate-slideInUp animate-delay-500">
                  <h3 className="text-lg font-semibold text-[color:var(--foreground)] mb-3 flex items-center">
                    <FontAwesomeIcon icon={faGraduationCap} className="mr-2 text-[color:var(--feature-yellow-text)]" />
                    {t('cv.education') || 'Education'}
                  </h3>
                  <div className="space-y-4">
                    {education.map((edu, index) => (
                      <div
                        key={index}
                        className="border border-[color:var(--border)] rounded-lg p-4 hover:bg-[color:var(--muted)]/20 transition-all duration-300 animate-slideInRight glass-effect cv-card-hover"
                        style={{ animationDelay: `${index * 100}ms` }}
                      >
                        <h4 className="font-semibold text-[color:var(--foreground)]">
                          {edu.degree_name} - {edu.institution_name}
                        </h4>
                        <div className="text-sm text-[color:var(--muted-foreground)] mt-1">
                          {edu.graduation_date && (
                            <span className="mr-4">
                              <FontAwesomeIcon icon={faClock} className="mr-1" />
                              {edu.graduation_date}
                            </span>
                          )}
                          {edu.gpa && (
                            <span>
                              <FontAwesomeIcon icon={faChartBar} className="mr-1" />
                              GPA: {edu.gpa}
                            </span>
                          )}
                        </div>
                        {edu.description && (
                          <p className="text-sm text-[color:var(--foreground)] mt-2">{edu.description}</p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Certificates */}
              {certificates.length > 0 && (
                <div className="animate-slideInUp animate-delay-600">
                  <h3 className="text-lg font-semibold text-[color:var(--foreground)] mb-3 flex items-center">
                    <FontAwesomeIcon icon={faCertificate} className="mr-2 text-[color:var(--feature-purple-text)]" />
                    {t('cv.certificates') || 'Certificates & Courses'}
                  </h3>
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {certificates.map((cert, index) => (
                      <div
                        key={index}
                        className="border border-[color:var(--border)] rounded-lg p-4 hover:bg-[color:var(--muted)]/20 transition-all duration-300 animate-bounceIn glass-effect cv-card-hover"
                        style={{ animationDelay: `${index * 100}ms` }}
                      >
                        <h4 className="font-semibold text-[color:var(--foreground)] mb-1">
                          {cert.certificate_name}
                        </h4>
                        <p className="text-sm text-[color:var(--muted-foreground)]">
                          {cert.issuing_organization}
                        </p>
                        {cert.issue_date && (
                          <p className="text-xs text-[color:var(--muted-foreground)] mt-1">
                            <FontAwesomeIcon icon={faClock} className="mr-1" />
                            {cert.issue_date}
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Projects Showcase */}
              {projects.length > 0 && (
                <div className="animate-slideInUp animate-delay-700">
                  <h3 className="text-lg font-semibold text-[color:var(--foreground)] mb-3 flex items-center">
                    <FontAwesomeIcon icon={faProjectDiagram} className="mr-2 text-[color:var(--feature-green-text)]" />
                    {t('cv.projects') || 'Projects'} ({projects.length})
                  </h3>
                  <div className="space-y-4">
                    {projects.map((project, index) => (
                      <div
                        key={index}
                        className="border border-[color:var(--border)] rounded-lg p-4 hover:bg-[color:var(--muted)]/20 transition-all duration-300 animate-slideInUp glass-effect cv-card-hover"
                        style={{ animationDelay: `${index * 100}ms` }}
                      >
                        <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-2">
                          <h4 className="font-semibold text-[color:var(--foreground)]">
                            {project.project_name}
                          </h4>
                          {project.project_url && (
                            <a 
                              href={project.project_url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="text-[color:var(--feature-blue-text)] hover:underline text-sm transition-colors duration-200"
                            >
                              <FontAwesomeIcon icon={faGlobe} className="mr-1" />
                              View Project
                            </a>
                          )}
                        </div>
                        {project.role && (
                          <p className="text-sm text-[color:var(--feature-purple-text)] font-medium mb-2">
                            Role: {project.role}
                          </p>
                        )}
                        {project.description && (
                          <p className="text-sm text-[color:var(--foreground)] mb-3">{project.description}</p>
                        )}
                        {project.technologies_used && project.technologies_used.length > 0 && (
                          <div className="mb-2">
                            <p className="text-xs text-[color:var(--muted-foreground)] mb-1">Technologies:</p>
                            <div className="flex flex-wrap gap-1">
                              {project.technologies_used.map((tech, techIndex) => (
                                <span
                                  key={techIndex}
                                  className="bg-[color:var(--muted)] text-[color:var(--foreground)] px-2 py-1 rounded text-xs"
                                >
                                  {tech}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                        {(project.start_date || project.end_date) && (
                          <div className="text-xs text-[color:var(--muted-foreground)]">
                            <FontAwesomeIcon icon={faClock} className="mr-1" />
                            {project.start_date} {project.end_date && `- ${project.end_date}`}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Inferred Characteristics */}
              {characteristics.length > 0 && (
                <div className="animate-slideInUp animate-delay-800">
                  <h3 className="text-lg font-semibold text-[color:var(--foreground)] mb-3 flex items-center">
                    <FontAwesomeIcon icon={faLightbulb} className="mr-2 text-[color:var(--feature-yellow-text)]" />
                    {t('cv.insights') || 'AI Insights & Characteristics'}
                  </h3>
                  <div className="space-y-4">
                    {characteristics.map((char, index) => (
                      <div
                        key={index}
                        className="border border-[color:var(--border)] rounded-lg p-4 hover:bg-[color:var(--muted)]/20 transition-all duration-300 animate-slideInRight glass-effect cv-card-hover"
                        style={{ animationDelay: `${index * 100}ms` }}
                      >
                        <div className="flex items-start mb-2">
                          <FontAwesomeIcon icon={faCheckCircle} className="text-[color:var(--feature-green-text)] mr-2 mt-1 flex-shrink-0" />
                          <div className="flex-1">
                            <h4 className="font-semibold text-[color:var(--foreground)] mb-1">
                              {char.characteristic_type}
                            </h4>
                            <p className="text-sm text-[color:var(--foreground)] mb-2">{char.statement}</p>
                            {char.evidence && char.evidence.length > 0 && (
                              <div>
                                <p className="text-xs text-[color:var(--muted-foreground)] mb-1">Evidence:</p>
                                <ul className="list-disc list-inside text-xs text-[color:var(--muted-foreground)] space-y-1">
                                  {char.evidence.map((evidence, evidenceIndex) => (
                                    <li key={evidenceIndex}>{evidence}</li>
                                  ))}
                                </ul>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Extracted Keywords */}
              {keywords.length > 0 && (
                <div className="animate-slideInUp animate-delay-900">
                  <h3 className="text-lg font-semibold text-[color:var(--foreground)] mb-3 flex items-center">
                    <FontAwesomeIcon icon={faHashtag} className="mr-2 text-[color:var(--feature-blue)]" />
                    {t('cv.keywords') || 'Keywords'} ({keywords.length})
                  </h3>
                  <div className="flex flex-wrap gap-2">                    {keywords.map((keyword, index) => (
                      <span
                        key={index}
                        className="bg-[color:var(--muted)] text-[color:var(--foreground)] px-3 py-1 rounded-full text-sm border border-[color:var(--border)] animate-fadeIn hover:bg-[color:var(--accent)] transition-all duration-200"
                        style={{ animationDelay: `${index * 30}ms` }}
                      >
                        #{typeof keyword === 'string' ? keyword : keyword.keyword}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* LLM Token Usage */}
              {tokenUsage && (
                <div className="animate-slideInUp animate-delay-1000">
                  <h3 className="text-lg font-semibold text-[color:var(--foreground)] mb-3 flex items-center">
                    <FontAwesomeIcon icon={faRobot} className="mr-2 text-[color:var(--feature-purple-text)]" />
                    {t('cv.analysisStats') || 'Analysis Statistics'}
                  </h3>
                  <div className="bg-[color:var(--muted)]/30 rounded-lg p-4 glass-effect">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="text-center hover:scale-105 transition-all duration-300">
                        <div className="text-xl font-bold text-[color:var(--feature-blue-text)]">
                          {tokenUsage.input_tokens?.toLocaleString() || 0}
                        </div>
                        <div className="text-sm text-[color:var(--muted-foreground)]">Input Tokens</div>
                      </div>
                      <div className="text-center hover:scale-105 transition-all duration-300">
                        <div className="text-xl font-bold text-[color:var(--feature-green-text)]">
                          {tokenUsage.output_tokens?.toLocaleString() || 0}
                        </div>
                        <div className="text-sm text-[color:var(--muted-foreground)]">Output Tokens</div>
                      </div>
                      <div className="text-center hover:scale-105 transition-all duration-300">
                        <div className="text-xl font-bold text-[color:var(--feature-purple-text)]">
                          {tokenUsage.total_tokens?.toLocaleString() || 0}
                        </div>
                        <div className="text-sm text-[color:var(--muted-foreground)]">Total Tokens</div>
                      </div>
                      <div className="text-center hover:scale-105 transition-all duration-300">
                        <div className="text-xl font-bold text-[color:var(--feature-yellow-text)]">
                          ${tokenUsage.price_usd?.toFixed(5) || '0.00000'}
                        </div>
                        <div className="text-sm text-[color:var(--muted-foreground)]">Cost (USD)</div>
                      </div>
                    </div>
                    <div className="mt-3 text-center">
                      <FontAwesomeIcon icon={faInfoCircle} className="text-[color:var(--muted-foreground)] mr-1" />
                      <span className="text-xs text-[color:var(--muted-foreground)]">
                        Analysis powered by AI with detailed token tracking
                      </span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </>
  )
}
