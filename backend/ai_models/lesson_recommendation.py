"""Utilities for lesson recommendation and analysis"""
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
from models import (
    db, User, Lesson, Course, Quiz, QuizResult, Topic, 
    LessonProgress, AIRecommendation, LearningAnalytics, Enrollment
)
from sqlalchemy import func, and_, or_
import json

logger = logging.getLogger(__name__)

class LessonRecommendationEngine:
    """Engine for generating intelligent lesson recommendations"""
    
    @staticmethod
    def get_user_weak_areas(user_id: int, course_id: Optional[int] = None) -> List[Dict]:
        """Identify weak areas based on quiz performance"""
        try:
            query = db.session.query(
                Topic.topic_id,
                Topic.topic_name,
                Topic.course_id,
                func.avg(QuizResult.score).label('avg_score'),
                func.count(QuizResult.result_id).label('attempt_count')
            ).join(
                Quiz, Topic.topic_id == Quiz.topic_id
            ).join(
                QuizResult, Quiz.quiz_id == QuizResult.quiz_id
            ).filter(
                QuizResult.user_id == user_id
            )
            
            if course_id:
                query = query.filter(Topic.course_id == course_id)
            
            weak_areas = query.group_by(
                Topic.topic_id, Topic.topic_name, Topic.course_id
            ).having(
                func.avg(QuizResult.score) < 70  # Less than 70%
            ).order_by(
                func.avg(QuizResult.score)
            ).all()
            
            return [{
                'topic_id': area.topic_id,
                'topic_name': area.topic_name,
                'course_id': area.course_id,
                'avg_score': float(area.avg_score) if area.avg_score else 0,
                'attempt_count': area.attempt_count
            } for area in weak_areas]
            
        except Exception as e:
            logger.error(f"[Recommendation] Error getting weak areas: {e}")
            return []
    
    @staticmethod
    def get_incomplete_lessons(user_id: int, course_id: Optional[int] = None) -> List[Dict]:
        """Get incomplete lessons for recommendation"""
        try:
            query = db.session.query(Lesson).filter(
                ~Lesson.lesson_id.in_(
                    db.session.query(LessonProgress.lesson_id).filter(
                        and_(
                            LessonProgress.user_id == user_id,
                            LessonProgress.is_completed == True
                        )
                    )
                )
            )
            
            if course_id:
                query = query.filter(Lesson.course_id == course_id)
            
            lessons = query.order_by(Lesson.lesson_order).all()
            return [lesson.to_dict() for lesson in lessons]
            
        except Exception as e:
            logger.error(f"[Recommendation] Error getting incomplete lessons: {e}")
            return []
    
    @staticmethod
    def get_progress_by_course(user_id: int) -> List[Dict]:
        """Get learning progress for each course"""
        try:
            enrollments = Enrollment.query.filter_by(user_id=user_id).all()
            progress_list = []
            
            for enrollment in enrollments:
                course = Course.query.get(enrollment.course_id)
                total_lessons = Lesson.query.filter_by(course_id=enrollment.course_id).count()
                completed_lessons = db.session.query(LessonProgress).filter(
                    and_(
                        LessonProgress.user_id == user_id,
                        LessonProgress.lesson_id.in_(
                            db.session.query(Lesson.lesson_id).filter(
                                Lesson.course_id == enrollment.course_id
                            )
                        ),
                        LessonProgress.is_completed == True
                    )
                ).count()
                
                progress_percentage = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
                
                progress_list.append({
                    'course_id': course.course_id,
                    'course_name': course.course_name,
                    'total_lessons': total_lessons,
                    'completed_lessons': completed_lessons,
                    'progress_percentage': progress_percentage,
                    'enrolled_at': enrollment.enrolled_at.isoformat() if enrollment.enrolled_at else None
                })
            
            return progress_list
            
        except Exception as e:
            logger.error(f"[Recommendation] Error getting progress: {e}")
            return []
    
    @staticmethod
    def generate_recommendations(user_id: int, course_id: Optional[int] = None) -> List[Dict]:
        """Generate comprehensive recommendations"""
        try:
            recommendations = []
            
            # 1. Weak areas - high priority
            weak_areas = LessonRecommendationEngine.get_user_weak_areas(user_id, course_id)
            for area in weak_areas:
                # Find lessons related to this topic
                lessons = Lesson.query.filter_by(
                    course_id=area['course_id']
                ).all()
                
                for lesson in lessons:
                    progress = LessonProgress.query.filter_by(
                        user_id=user_id,
                        lesson_id=lesson.lesson_id
                    ).first()
                    
                    if not progress or not progress.is_completed:
                        recommendations.append({
                            'type': 'weak_area_review',
                            'priority': 1,  # Highest
                            'lesson_id': lesson.lesson_id,
                            'lesson_title': lesson.lesson_title,
                            'course_id': area['course_id'],
                            'topic_name': area['topic_name'],
                            'reason': f"Bạn có điểm trung bình {area['avg_score']:.1f}% cho chủ đề '{area['topic_name']}'. Hãy ôn lại bài học này.",
                            'avg_score': area['avg_score']
                        })
            
            # 2. Incomplete lessons - medium priority
            incomplete_lessons = LessonRecommendationEngine.get_incomplete_lessons(user_id, course_id)
            for lesson in incomplete_lessons:
                # Check if this lesson hasn't been started
                progress = LessonProgress.query.filter_by(
                    user_id=user_id,
                    lesson_id=lesson['lesson_id']
                ).first()
                
                if not progress:
                    recommendations.append({
                        'type': 'incomplete_lesson',
                        'priority': 2,  # Medium
                        'lesson_id': lesson['lesson_id'],
                        'lesson_title': lesson['lesson_title'],
                        'course_id': lesson['course_id'],
                        'reason': "Bạn chưa bắt đầu bài học này. Hãy hoàn thành để tiến bộ."
                    })
            
            # 3. Recently accessed but not completed - medium priority
            recent_progress = LessonProgress.query.filter(
                and_(
                    LessonProgress.user_id == user_id,
                    LessonProgress.is_completed == False,
                    LessonProgress.last_accessed >= datetime.utcnow() - timedelta(days=7)
                )
            ).order_by(LessonProgress.last_accessed.desc()).limit(3).all()
            
            for progress in recent_progress:
                lesson = Lesson.query.get(progress.lesson_id)
                recommendations.append({
                    'type': 'in_progress',
                    'priority': 2,
                    'lesson_id': lesson.lesson_id,
                    'lesson_title': lesson.lesson_title,
                    'course_id': lesson.course_id,
                    'reason': f"Bạn vừa mới truy cập bài học này. Tiếp tục hoàn thành nó.",
                    'time_spent': progress.time_spent_minutes
                })
            
            # Sort by priority and remove duplicates
            seen_lessons = set()
            unique_recommendations = []
            for rec in sorted(recommendations, key=lambda x: x['priority']):
                if rec['lesson_id'] not in seen_lessons:
                    seen_lessons.add(rec['lesson_id'])
                    unique_recommendations.append(rec)
            
            logger.info(f"[Recommendation] Generated {len(unique_recommendations)} recommendations for user {user_id}")
            return unique_recommendations[:10]  # Return top 10
            
        except Exception as e:
            logger.error(f"[Recommendation] Error generating recommendations: {e}")
            return []


class LearningAnalyticsEngine:
    """Engine for analyzing learning patterns and progress"""
    
    @staticmethod
    def analyze_learning_patterns(user_id: int, course_id: Optional[int] = None) -> Dict:
        """Analyze user's learning patterns"""
        try:
            # Get all quiz results
            query = db.session.query(QuizResult).filter(
                QuizResult.user_id == user_id
            )
            
            if course_id:
                query = query.join(
                    Quiz, QuizResult.quiz_id == Quiz.quiz_id
                ).filter(Quiz.course_id == course_id)
            
            quiz_results = query.all()
            
            if not quiz_results:
                return {
                    'total_quizzes': 0,
                    'average_score': 0,
                    'best_score': 0,
                    'worst_score': 0,
                    'total_time_minutes': 0,
                    'improvement_trend': 'insufficient_data'
                }
            
            scores = [float(q.score) if q.score else 0 for q in quiz_results]
            
            # Calculate statistics
            avg_score = sum(scores) / len(scores)
            best_score = max(scores)
            worst_score = min(scores)
            total_time = sum([q.time_taken_minutes or 0 for q in quiz_results])
            
            # Calculate improvement trend (last 3 vs first 3)
            trend = 'stable'
            if len(scores) >= 6:
                first_avg = sum(scores[:3]) / 3
                last_avg = sum(scores[-3:]) / 3
                if last_avg > first_avg + 5:
                    trend = 'improving'
                elif last_avg < first_avg - 5:
                    trend = 'declining'
            
            return {
                'total_quizzes': len(quiz_results),
                'average_score': avg_score,
                'best_score': best_score,
                'worst_score': worst_score,
                'total_time_minutes': total_time,
                'improvement_trend': trend,
                'scores': scores
            }
            
        except Exception as e:
            logger.error(f"[Analytics] Error analyzing patterns: {e}")
            return {}
    
    @staticmethod
    def get_strengths_and_weaknesses(user_id: int) -> Dict:
        """Identify learning strengths and weaknesses"""
        try:
            topics_stats = db.session.query(
                Topic.topic_id,
                Topic.topic_name,
                func.avg(QuizResult.score).label('avg_score'),
                func.count(QuizResult.result_id).label('attempt_count')
            ).join(
                Quiz, Topic.topic_id == Quiz.topic_id
            ).join(
                QuizResult, Quiz.quiz_id == QuizResult.quiz_id
            ).filter(
                QuizResult.user_id == user_id
            ).group_by(
                Topic.topic_id, Topic.topic_name
            ).all()
            
            strengths = []
            weaknesses = []
            
            for stat in topics_stats:
                topic_data = {
                    'topic_id': stat.topic_id,
                    'topic_name': stat.topic_name,
                    'avg_score': float(stat.avg_score) if stat.avg_score else 0,
                    'attempt_count': stat.attempt_count
                }
                
                if stat.avg_score and stat.avg_score >= 80:
                    strengths.append(topic_data)
                elif stat.avg_score and stat.avg_score < 60:
                    weaknesses.append(topic_data)
            
            return {
                'strengths': sorted(strengths, key=lambda x: x['avg_score'], reverse=True),
                'weaknesses': sorted(weaknesses, key=lambda x: x['avg_score'])
            }
            
            
        except Exception as e:
            logger.error(f"[Analytics] Error getting strengths/weaknesses: {e}")
            return {'strengths': [], 'weaknesses': []}


class IncorrectAnswerRecommendationEngine:
    """Engine để phân tích câu trả lời sai và gợi ý bài học"""
    
    @staticmethod
    def analyze_incorrect_answer(user_id: int, question_id: int, user_answer: int,
                                 correct_answer: int, quiz_id: int) -> Optional[Dict]:
        """
        Phân tích một câu trả lời sai và gợi ý bài học cần ôn
        """
        from models import QuizQuestion, IncorrectAnswerAnalysis, Lesson, Topic
        
        try:
            # Lấy thông tin câu hỏi
            question = QuizQuestion.query.get(question_id)
            if not question:
                return None
            
            # Kiểm tra xem đã phân tích lần này chưa
            existing = IncorrectAnswerAnalysis.query.filter_by(
                user_id=user_id,
                question_id=question_id,
                quiz_id=quiz_id
            ).first()
            
            if existing:
                return existing.to_dict()
            
            # Lấy lesson liên quan
            lesson = None
            if question.course_id:
                lessons = Lesson.query.filter_by(course_id=question.course_id).all()
                lesson = lessons[0] if lessons else None
            
            # Đếm bao nhiêu lần sinh viên sai câu này
            similar_wrong = IncorrectAnswerAnalysis.query.filter_by(
                user_id=user_id,
                question_id=question_id
            ).count()
            
            # Xác định loại lỗi (dùng AI để phân tích sau)
            error_type = 'conceptual'  # Default
            if similar_wrong > 2:
                error_type = 'systematic'  # Sai liên tục
            
            # Tìm các bài học liên quan
            recommended_lessons = []
            if question.topic_id:
                topic = Topic.query.get(question.topic_id)
                if topic and question.course_id:
                    related_lessons = Lesson.query.filter_by(
                        course_id=question.course_id
                    ).order_by(Lesson.lesson_order).limit(3).all()
                    recommended_lessons = [l.lesson_id for l in related_lessons]
            
            # Tạo bản ghi phân tích
            analysis = IncorrectAnswerAnalysis(
                user_id=user_id,
                question_id=question_id,
                topic_id=question.topic_id,
                course_id=question.course_id,
                lesson_id=lesson.lesson_id if lesson else None,
                quiz_id=quiz_id,
                question_text=question.question_text,
                user_answer=user_answer,
                correct_answer=correct_answer,
                difficulty_level=question.difficulty_level,
                error_type=error_type,
                recommended_lessons=json.dumps(recommended_lessons),
                times_similar_wrong=similar_wrong,
                ai_analysis=f"Sinh viên đã trả lời sai {similar_wrong + 1} lần. Có thể là lỗi khái niệm.",
                analyzed_at=datetime.utcnow()
            )
            
            db.session.add(analysis)
            db.session.commit()
            
            logger.info(f"[IncorrectAnswer] Analyzed incorrect answer - User: {user_id}, Question: {question_id}")
            return analysis.to_dict()
            
        except Exception as e:
            logger.error(f"[IncorrectAnswer] Error analyzing: {e}")
            return None
    
    @staticmethod
    def get_incorrect_answer_insights(user_id: int, course_id: Optional[int] = None,
                                     limit: int = 10) -> List[Dict]:
        """
        Lấy danh sách những câu trả lời sai gần đây và gợi ý bài học
        """
        from models import IncorrectAnswerAnalysis, Lesson
        
        try:
            query = IncorrectAnswerAnalysis.query.filter_by(user_id=user_id)
            
            if course_id:
                query = query.filter_by(course_id=course_id)
            
            # Lấy những lỗi gần đây nhất
            incorrect_answers = query.order_by(
                IncorrectAnswerAnalysis.created_at.desc()
            ).limit(limit).all()
            
            insights = []
            for answer in incorrect_answers:
                recommended_lesson_details = []
                
                if answer.recommended_lessons:
                    try:
                        lesson_ids = json.loads(answer.recommended_lessons)
                        for lid in lesson_ids:
                            lesson = Lesson.query.get(lid)
                            if lesson:
                                recommended_lesson_details.append({
                                    'lesson_id': lesson.lesson_id,
                                    'lesson_title': lesson.lesson_title,
                                    'duration_minutes': lesson.duration_minutes
                                })
                    except Exception as e:
                        logger.debug(f"[IncorrectAnswer] Failed to parse recommended_lessons JSON: {e}")
                
                insights.append({
                    'analysis_id': answer.analysis_id,
                    'question_text': answer.question_text,
                    'error_type': answer.error_type,
                    'times_wrong': answer.times_similar_wrong + 1,
                    'ai_analysis': answer.ai_analysis,
                    'recommended_lessons': recommended_lesson_details,
                    'wrong_at': answer.created_at.isoformat()
                })
            
            logger.info(f"[IncorrectAnswer] Retrieved {len(insights)} insights for user {user_id}")
            return insights
            
        except Exception as e:
            logger.error(f"[IncorrectAnswer] Error getting insights: {e}")
            return []
    
    @staticmethod
    def get_common_mistakes_by_topic(course_id: int, topic_id: Optional[int] = None,
                                    limit: int = 5) -> List[Dict]:
        """
        Lấy những lỗi thường gặp theo chủ đề (cho giáo viên)
        """
        from models import IncorrectAnswerAnalysis, Topic
        from sqlalchemy import func
        
        try:
            query = db.session.query(
                IncorrectAnswerAnalysis.topic_id,
                IncorrectAnswerAnalysis.error_type,
                func.count(IncorrectAnswerAnalysis.analysis_id).label('mistake_count'),
                func.count(db.func.distinct(IncorrectAnswerAnalysis.user_id)).label('affected_students')
            ).filter(IncorrectAnswerAnalysis.course_id == course_id)
            
            if topic_id:
                query = query.filter(IncorrectAnswerAnalysis.topic_id == topic_id)
            
            mistakes = query.group_by(
                IncorrectAnswerAnalysis.topic_id,
                IncorrectAnswerAnalysis.error_type
            ).order_by(
                func.count(IncorrectAnswerAnalysis.analysis_id).desc()
            ).limit(limit).all()
            
            result = []
            for mistake in mistakes:
                topic = Topic.query.get(mistake.topic_id)
                result.append({
                    'topic_id': mistake.topic_id,
                    'topic_name': topic.topic_name if topic else 'Unknown',
                    'error_type': mistake.error_type,
                    'total_mistakes': mistake.mistake_count,
                    'affected_students': mistake.affected_students,
                    'severity': 'high' if mistake.mistake_count > 5 else 'medium' if mistake.mistake_count > 2 else 'low'
                })
            
            return result
            
        except Exception as e:
            logger.error(f"[IncorrectAnswer] Error getting common mistakes: {e}")
            return []

