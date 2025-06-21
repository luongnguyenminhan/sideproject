"""
Question composer repository layer.
"""

import logging
import uuid
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from fastapi import Depends

from app.core.database import get_db
from app.exceptions.exception import (
    NotFoundException,
    ValidationException,
    CustomHTTPException,
)
from app.middleware.translation_manager import _

from ..dal.question_session_dal import QuestionSessionDAL
from ..workflows.question_generation import QuestionGenerationWorkflow
from ..workflows.question_generation.config.workflow_config import (
    QuestionGenerationWorkflowConfig,
)
from ..schemas.question_request import (
    QuestionGenerationRequest,
    AnalyzeUserProfileRequest,
    SearchQuestionSessionsRequest,
)
from ..schemas.question_response import (
    QuestionGenerationResponse,
    UserProfileAnalysisResponse,
    QuestionSessionResponse,
)
from ..schemas.question_schemas import UserProfile, Question

logger = logging.getLogger(__name__)


class QuestionComposerRepo:
    """
    Repository layer for question composer module.

    Handles business logic for question generation and user profile analysis.
    """

    def __init__(self, db: Session = Depends(get_db)):
        logger.info("🚀 Initializing QuestionComposerRepo")
        self.db = db
        logger.info("📊 Database session established")

        self.question_session_dal = QuestionSessionDAL(db)
        logger.info("🗄️ QuestionSessionDAL initialized")

        # Initialize workflow
        logger.info("⚙️ Loading QuestionGenerationWorkflowConfig from environment")
        self.config = QuestionGenerationWorkflowConfig.from_env()
        logger.info(
            f'🔧 Config loaded - LLM: {getattr(self.config, "llm_model", "N/A")}, Max iterations: {getattr(self.config, "max_iterations", "N/A")}'
        )

        self.workflow = QuestionGenerationWorkflow(self.config)
        logger.info("🔄 QuestionGenerationWorkflow initialized successfully")

        logger.info("✅ QuestionComposerRepo initialization complete")

    async def generate_questions(
        self, request: QuestionGenerationRequest
    ) -> QuestionGenerationResponse:
        """
        Generate intelligent questions based on user profile and history.
        """
        logger.info("🎯 Starting question generation process")
        logger.info(
            f"📝 Request details - User ID: {request.user_id}, Session ID: {request.session_id}, Max iterations: {request.max_iterations}, Previous questions count: {len(request.previous_questions or [])}"
        )

        try:
            # Generate or use existing session_id
            session_id = request.session_id or str(uuid.uuid4())
            logger.info(f"🆔 Working with session ID: {session_id}")

            if not request.session_id:
                logger.info("🆕 No session ID provided, generated new one")
            else:
                logger.info("🔄 Using existing session ID from request")

            # Get or create session
            logger.info(f"🔍 Searching for existing session: {session_id}")
            session = self.question_session_dal.get_by_session_id(session_id)

            if not session:
                logger.info("📝 No existing session found, creating new session")
                session = self._create_new_session(request, session_id)
                logger.info(
                    f"✅ New session created with ID: {session.id}, Status: {session.status}"
                )
            else:
                logger.info(
                    f"🔄 Found existing session - ID: {session.id}, Status: {session.status}, Current iteration: {session.current_iteration}/{session.max_iterations}, Total questions: {session.total_questions_generated}"
                )

            # Validate session can continue
            logger.info("🔒 Validating session status")
            if session.status == "completed":
                logger.warning(f"❌ Session {session_id} is already completed")
                raise ValidationException(_("session_already_completed"))

            if session.status == "error":
                logger.warning(
                    f"❌ Session {session_id} is in error state: {session.error_message}"
                )
                raise ValidationException(_("session_in_error_state"))

            logger.info("✅ Session validation passed")

            # Prepare user profile
            logger.info("👤 Preparing user profile data")
            user_profile_data = request.existing_user_data or {}
            logger.info(f"📊 User profile data keys: {list(user_profile_data.keys())}")
            user_profile = UserProfile(**user_profile_data)
            logger.info("✅ User profile object created successfully")

            # Convert previous questions to proper format
            logger.info("📋 Processing previous questions")
            previous_questions = []
            if request.previous_questions:
                logger.info(
                    f"🔄 Converting {len(request.previous_questions)} previous questions"
                )
                previous_questions = [Question(**q) for q in request.previous_questions]
                logger.info(
                    f"✅ Successfully converted {len(previous_questions)} questions"
                )
                for i, q in enumerate(previous_questions):
                    logger.info(
                        f"  📝 Question {i + 1}: Type={q.Question_type}, Text length={len(q.Question)}"
                    )
            else:
                logger.info("📋 No previous questions to process")

            # Run workflow
            logger.info(
                f"🚀 Starting question generation workflow for session: {session_id}"
            )
            logger.info(
                f"⚙️ Workflow parameters - User profile completeness estimate: {len(user_profile_data)} fields, Previous questions: {len(previous_questions)}"
            )

            workflow_result = await self.workflow.generate_questions(
                user_profile=user_profile,
                existing_questions=previous_questions,
                session_id=session_id,
            )

            logger.info("✅ Workflow execution completed successfully")
            logger.info(
                f"📊 Workflow results - Generated questions: {len(workflow_result.questions)}, Completeness score: {workflow_result.completeness_score:.3f}, Should continue: {workflow_result.should_continue}"
            )

            # Log each generated question
            for i, question in enumerate(workflow_result.questions):
                logger.info(
                    f'  📝 Generated Question {i + 1}: Type={question.Question_type}, Category={getattr(question, "category", "N/A")}, Text length={len(question.Question)}'
                )

            logger.info(f"🎯 Next focus areas: {workflow_result.next_focus_areas}")
            logger.info(
                f"📈 Analysis: {workflow_result.analysis[:100]}..."
                if len(workflow_result.analysis) > 100
                else f"📈 Analysis: {workflow_result.analysis}"
            )

            # Update session with results
            logger.info("💾 Updating session with workflow results")
            self._update_session_with_results(session, workflow_result)
            logger.info("✅ Session updated successfully")

            # Convert to response format
            logger.info("🔄 Converting workflow results to response format")
            response = QuestionGenerationResponse(
                session_id=session_id,
                questions=[q.model_dump() for q in workflow_result.questions],
                analysis=workflow_result.analysis,
                next_focus_areas=workflow_result.next_focus_areas,
                completeness_score=workflow_result.completeness_score,
                should_continue=workflow_result.should_continue,
                current_iteration=session.current_iteration,
                total_questions_generated=session.total_questions_generated,
            )

            logger.info(f"🎉 Question generation completed successfully!")
            logger.info(
                f"📊 Final response summary - Session: {session_id}, Questions generated: {len(response.questions)}, Completeness: {response.completeness_score:.3f}, Continue: {response.should_continue}, Iteration: {response.current_iteration}"
            )

            return response

        except ValidationException as e:
            logger.error(f"❌ Validation error in question generation: {str(e)}")
            raise
        except Exception as e:
            logger.error(
                f"💥 Unexpected error in question generation: {str(e)}", exc_info=True
            )
            # Mark session as error if it exists
            if "session_id" in locals():
                logger.info(f"🚨 Marking session {session_id} as error state")
                self.question_session_dal.mark_session_error(session_id, str(e))
                logger.info("✅ Session marked as error")
            raise CustomHTTPException(message=_("question_generation_failed"))

    async def analyze_user_profile(
        self, request: AnalyzeUserProfileRequest
    ) -> UserProfileAnalysisResponse:
        """
        Analyze user profile completeness without generating new questions.
        """
        logger.info("🔍 Starting user profile analysis")
        logger.info(
            f"📊 Analysis request - User profile provided: {bool(request.user_profile)}, Previous questions count: {len(request.previous_questions or [])}"
        )

        try:
            # Validate request
            logger.info("🔒 Validating analysis request")
            if not request.user_profile:
                logger.warning("❌ User profile is required but not provided")
                raise ValidationException(_("user_profile_required"))

            logger.info("✅ Request validation passed")

            # Prepare user profile
            logger.info("👤 Preparing user profile for analysis")
            logger.info(
                f"📋 User profile data keys: {list(request.user_profile.keys())}"
            )
            user_profile = UserProfile(**request.user_profile)
            logger.info("✅ User profile object created successfully")

            # Convert previous questions
            logger.info("📋 Processing previous questions for analysis")
            previous_questions = []
            if request.previous_questions:
                logger.info(
                    f"🔄 Converting {len(request.previous_questions)} previous questions"
                )
                previous_questions = [Question(**q) for q in request.previous_questions]
                logger.info(
                    f"✅ Successfully converted {len(previous_questions)} questions"
                )

                # Log question type distribution
                question_types = {}
                for q in previous_questions:
                    question_types[q.Question_type] = (
                        question_types.get(q.Question_type, 0) + 1
                    )
                logger.info(f"📊 Question type distribution: {question_types}")
            else:
                logger.info("📋 No previous questions to analyze")

            # Use workflow for analysis
            temp_session_id = str(uuid.uuid4())
            logger.info(
                f"🔬 Running profile completeness analysis with temp session: {temp_session_id}"
            )

            analysis_result = await self.workflow.analyze_user_completeness(
                user_profile, previous_questions
            )

            logger.info("✅ Profile analysis completed successfully")
            logger.info(f"📊 Analysis results summary:")
            logger.info(
                f'  📈 Completeness score: {analysis_result.get("completeness_score", 0.0):.3f}'
            )
            logger.info(
                f'  🎯 Missing areas count: {len(analysis_result.get("missing_areas", []))}'
            )
            logger.info(
                f'  📝 Analysis length: {len(analysis_result.get("analysis", ""))} characters'
            )
            logger.info(
                f'  🔄 Should continue: {analysis_result.get("should_continue", True)}'
            )

            missing_areas = analysis_result.get("missing_areas", [])
            if missing_areas:
                logger.info(f"  🎯 Missing areas: {missing_areas}")
            else:
                logger.info("  ✅ No missing areas identified")

            response = UserProfileAnalysisResponse(
                completeness_score=analysis_result.get("completeness_score", 0.0),
                missing_areas=missing_areas,
                analysis=analysis_result.get("analysis", ""),
                should_continue=analysis_result.get("should_continue", True),
                suggested_focus=missing_areas,
            )

            logger.info(f"🎉 User profile analysis completed successfully!")
            logger.info(f"📊 Final analysis score: {response.completeness_score:.3f}")

            return response

        except ValidationException as e:
            logger.error(f"❌ Validation error in profile analysis: {str(e)}")
            raise
        except Exception as e:
            logger.error(
                f"💥 Unexpected error in profile analysis: {str(e)}", exc_info=True
            )
            raise CustomHTTPException(message=_("profile_analysis_failed"))

    def get_question_session(self, session_id: str) -> QuestionSessionResponse:
        """
        Get question session by ID.
        """
        logger.info(f"🔍 Retrieving question session: {session_id}")

        session = self.question_session_dal.get_by_session_id(session_id)
        if not session:
            logger.warning(f"❌ Session not found: {session_id}")
            raise NotFoundException(_("session_not_found"))

        logger.info(
            f"✅ Session found - ID: {session.id}, Status: {session.status}, Iteration: {session.current_iteration}/{session.max_iterations}"
        )
        logger.info(
            f"📊 Session stats - Questions generated: {session.total_questions_generated}, Completeness: {session.completeness_score:.3f}"
        )

        response = QuestionSessionResponse(
            id=session.id,
            session_id=session.session_id,
            user_id=session.user_id,
            status=session.status,
            current_iteration=session.current_iteration,
            max_iterations=session.max_iterations,
            completeness_score=session.completeness_score,
            should_continue=session.should_continue,
            workflow_complete=session.info,
            total_questions_generated=session.total_questions_generated,
            missing_areas=session.missing_areas,
            focus_areas=session.focus_areas,
            error_message=session.error_message,
            create_date=(
                session.create_date.isoformat() if session.create_date else None
            ),
            update_date=(
                session.update_date.isoformat() if session.update_date else None
            ),
        )

        logger.info(f"🎉 Session retrieved successfully: {session_id}")
        return response

    def search_question_sessions(
        self, request: SearchQuestionSessionsRequest
    ) -> List[QuestionSessionResponse]:
        """
        Search question sessions with filtering.
        """
        logger.info("🔍 Starting question sessions search")
        logger.info(
            f"🔎 Search criteria - Session ID: {request.session_id}, User ID: {request.user_id}, Status: {request.status}"
        )

        try:
            # Get sessions based on filters
            sessions = []

            if request.session_id:
                logger.info(f"🎯 Searching by session ID: {request.session_id}")
                session = self.question_session_dal.get_by_session_id(
                    request.session_id
                )
                sessions = [session] if session else []
                logger.info(f"📊 Found {len(sessions)} session(s) by session ID")

            elif request.user_id:
                logger.info(f"👤 Searching by user ID: {request.user_id}")
                sessions = self.question_session_dal.get_by_user_id(request.user_id)
                logger.info(f"📊 Found {len(sessions)} session(s) for user")

            elif request.status:
                logger.info(f"📋 Searching by status: {request.status}")
                sessions = self.question_session_dal.get_by_status(request.status)
                logger.info(f"📊 Found {len(sessions)} session(s) with status")

            else:
                logger.info("🔄 Getting all active sessions (no specific filter)")
                sessions = self.question_session_dal.get_active_sessions()
                logger.info(f"📊 Found {len(sessions)} active session(s)")

            # Log session details
            if sessions:
                logger.info("📋 Session details:")
                for i, session in enumerate(sessions):
                    logger.info(
                        f"  Session {i + 1}: ID={session.session_id}, Status={session.status}, User={session.user_id}, Questions={session.total_questions_generated}"
                    )

            # Convert to response format
            logger.info("🔄 Converting sessions to response format")
            responses = []
            for session in sessions:
                response = QuestionSessionResponse(
                    id=session.id,
                    session_id=session.session_id,
                    user_id=session.user_id,
                    status=session.status,
                    current_iteration=session.current_iteration,
                    max_iterations=session.max_iterations,
                    completeness_score=session.completeness_score,
                    should_continue=session.should_continue,
                    workflow_complete=session.info,
                    total_questions_generated=session.total_questions_generated,
                    missing_areas=session.missing_areas,
                    focus_areas=session.focus_areas,
                    error_message=session.error_message,
                    create_date=(
                        session.create_date.isoformat() if session.create_date else None
                    ),
                    update_date=(
                        session.update_date.isoformat() if session.update_date else None
                    ),
                )
                responses.append(response)

            logger.info(
                f"🎉 Session search completed successfully! Returned {len(responses)} session(s)"
            )
            return responses

        except Exception as e:
            logger.error(
                f"💥 Error searching question sessions: {str(e)}", exc_info=True
            )
            raise CustomHTTPException(message=_("session_search_failed"))

    def get_service_info(self) -> Dict[str, Any]:
        """Get repository and workflow information"""
        logger.info("ℹ️ Retrieving service information")

        try:
            workflow_info = self.workflow.get_workflow_info()
            config_dict = self.config.to_dict()

            service_info = {
                "name": "Question Composer Repository",
                "version": "1.0.0",
                "workflow_info": workflow_info,
                "config": config_dict,
                "features": [
                    "Intelligent question generation",
                    "User profile analysis",
                    "Session management",
                    "Adaptive questioning based on completeness",
                    "4 question types support",
                    "Vietnamese language optimized",
                    "LangGraph workflow integration",
                    "Database persistence",
                ],
            }

            logger.info("✅ Service information retrieved successfully")
            logger.info(f"🔧 Config keys: {list(config_dict.keys())}")
            logger.info(f"⚙️ Workflow info keys: {list(workflow_info.keys())}")

            return service_info

        except Exception as e:
            logger.error(f"💥 Error retrieving service info: {str(e)}", exc_info=True)
            return {
                "name": "Question Composer Repository",
                "version": "1.0.0",
                "error": f"Failed to retrieve full info: {str(e)}",
            }

    def _create_new_session(self, request: QuestionGenerationRequest, session_id: str):
        """Create new question session"""
        logger.info(f"📝 Creating new session with ID: {session_id}")
        logger.info(
            f"👤 Session details - User ID: {request.user_id}, Max iterations: {request.max_iterations}"
        )
        logger.info(f"🎯 Focus areas: {request.focus_areas}")
        logger.info(
            f"📊 Existing user data keys: {list((request.existing_user_data or {}).keys())}"
        )

        session_data = {
            "session_id": session_id,
            "user_id": request.user_id,
            "status": "active",
            "current_iteration": 0,
            "max_iterations": request.max_iterations,
            "user_profile_data": request.existing_user_data or {},
            "existing_user_data": request.existing_user_data or {},
            "generated_questions": [],
            "all_previous_questions": request.previous_questions or [],
            "completeness_score": 0.0,
            "missing_areas": [],
            "focus_areas": request.focus_areas or [],
            "should_continue": True,
            "workflow_complete": False,
            "total_questions_generated": len(request.previous_questions or []),
        }

        logger.info(f"💾 Saving session data to database")
        session = self.question_session_dal.create(session_data)
        logger.info(f"✅ New session created successfully with DB ID: {session.id}")

        return session

    def _update_session_with_results(self, session, workflow_result):
        """Update session with workflow results"""
        logger.info(f"💾 Updating session {session.session_id} with workflow results")
        logger.info(
            f"📊 Update data - New iteration: {session.current_iteration + 1}, Completeness: {workflow_result.completeness_score:.3f}, Should continue: {workflow_result.should_continue}"
        )

        # Update session progress
        logger.info("🔄 Updating session progress")
        self.question_session_dal.update_session_progress(
            session.session_id,
            session.current_iteration + 1,
            workflow_result.completeness_score,
            workflow_result.should_continue,
        )
        logger.info("✅ Session progress updated")

        # Save generated questions
        logger.info(f"📝 Saving {len(workflow_result.questions)} generated questions")
        all_questions = (session.all_previous_questions or []) + [
            q.dict() for q in workflow_result.questions
        ]
        logger.info(f"📊 Total questions after update: {len(all_questions)}")

        self.question_session_dal.save_generated_questions(
            session.session_id,
            [q.dict() for q in workflow_result.questions],
            all_questions,
        )
        logger.info("✅ Generated questions saved")

        # Save analysis results
        logger.info("📈 Saving analysis results")
        analysis_decision = {
            "analysis": workflow_result.analysis,
            "completeness_score": workflow_result.completeness_score,
            "should_continue": workflow_result.should_continue,
        }

        logger.info(
            f"🎯 Focus areas for next iteration: {workflow_result.next_focus_areas}"
        )

        self.question_session_dal.save_analysis_result(
            session.session_id,
            analysis_decision,
            [],  # missing_areas will be extracted from workflow_result if available
            workflow_result.next_focus_areas,
        )
        logger.info("✅ Analysis results saved")
        logger.info(f"🎉 Session {session.session_id} update completed successfully")
