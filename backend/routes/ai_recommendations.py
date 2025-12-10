from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from utils import get_current_user_id
from models import db, User, AIRecommendation, Lesson, Course, QuizResult, Topic, LessonProgress, Enrollment
from ai_models.lesson_recommendation import LessonRecommendationEngine, LearningAnalyticsEngine
from datetime import datetime
import logging

bp = Blueprint('ai_recommendations', __name__)
logger = logging.getLogger(__name__)

@bp.route('/get-recommendations', methods=['GET'])
@jwt_required()
def get_recommendations():
    """
    Get intelligent lesson recommendations for user
    Query params:
    - course_id: Optional course filter
    - include_analytics: Include learning analytics (true/false)
    """
    try:
        user_id = get_current_user_id()
        course_id = request.args.get('course_id', type=int)
        include_analytics = request.args.get('include_analytics', 'false').lower() == 'true'
        
        # Get recommendations using the recommendation engine
        recommendations = LessonRecommendationEngine.generate_recommendations(user_id, course_id)
        
        result = {
            'recommendations': recommendations,
            'total_recommendations': len(recommendations)
        }
        
        # Include analytics if requested
        if include_analytics:
            analytics = LearningAnalyticsEngine.analyze_learning_patterns(user_id, course_id)
            strengths_weaknesses = LearningAnalyticsEngine.get_strengths_and_weaknesses(user_id)
            progress = LessonRecommendationEngine.get_progress_by_course(user_id)
            
            result['analytics'] = {
                'patterns': analytics,
                'strengths': strengths_weaknesses.get('strengths', []),
                'weaknesses': strengths_weaknesses.get('weaknesses', []),
                'course_progress': progress
            }
        
        logger.info(f"[Recommendations] Retrieved {len(recommendations)} recommendations for user {user_id}")
        return jsonify(result), 200
        
    except Exception as e:
        logger.error(f"[Recommendations] Error: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/get-analytics', methods=['GET'])
@jwt_required()
def get_learning_analytics():
    """
    Get comprehensive learning analytics for user
    Query params:
    - course_id: Optional course filter
    """
    try:
        user_id = get_current_user_id()
        course_id = request.args.get('course_id', type=int)
        
        # Get analytics
        patterns = LearningAnalyticsEngine.analyze_learning_patterns(user_id, course_id)
        strengths_weaknesses = LearningAnalyticsEngine.get_strengths_and_weaknesses(user_id)
        progress = LessonRecommendationEngine.get_progress_by_course(user_id)
        weak_areas = LessonRecommendationEngine.get_user_weak_areas(user_id, course_id)
        
        return jsonify({
            'learning_patterns': patterns,
            'strengths': strengths_weaknesses.get('strengths', []),
            'weaknesses': strengths_weaknesses.get('weaknesses', []),
            'weak_areas': weak_areas,
            'course_progress': progress
        }), 200
        
    except Exception as e:
        logger.error(f"[Analytics] Error: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/get-weak-areas', methods=['GET'])
@jwt_required()
def get_weak_areas():
    """
    Get topics where user has weak performance
    Query params:
    - course_id: Optional course filter
    """
    try:
        user_id = get_current_user_id()
        course_id = request.args.get('course_id', type=int)
        
        weak_areas = LessonRecommendationEngine.get_user_weak_areas(user_id, course_id)
        
        return jsonify({
            'weak_areas': weak_areas,
            'total_weak_areas': len(weak_areas)
        }), 200
        
    except Exception as e:
        logger.error(f"[WeakAreas] Error: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('/get-progress', methods=['GET'])
@jwt_required()
def get_progress():
    """Get learning progress across all courses"""
    try:
        user_id = get_current_user_id()
        
        progress = LessonRecommendationEngine.get_progress_by_course(user_id)
        
        # Calculate overall stats
        total_lessons = sum(p['total_lessons'] for p in progress)
        completed_lessons = sum(p['completed_lessons'] for p in progress)
        overall_progress = (completed_lessons / total_lessons * 100) if total_lessons > 0 else 0
        
        return jsonify({
            'overall_progress': overall_progress,
            'total_lessons': total_lessons,
            'completed_lessons': completed_lessons,
            'courses': progress
        }), 200
        
    except Exception as e:
        logger.error(f"[Progress] Error: {e}")
        return jsonify({'error': str(e)}), 500


# Legacy endpoints for backward compatibility
@bp.route('/generate', methods=['POST'])
@jwt_required()
def generate_recommendations_legacy():
    """Legacy recommendation generation endpoint"""
    try:
        user_id = get_current_user_id()
        course_id = request.json.get('course_id') if request.json else None
        
        recommendations = LessonRecommendationEngine.generate_recommendations(user_id, course_id)
        
        logger.info(f"[Recommendations] Generated {len(recommendations)} recommendations")
        
        return jsonify({
            'message': f'Generated {len(recommendations)} recommendations',
            'count': len(recommendations),
            'recommendations': recommendations
        }), 200
        
    except Exception as e:
        logger.error(f"[Recommendations] Error: {e}")
        return jsonify({'error': str(e)}), 500


@bp.route('', methods=['GET'])
@jwt_required()
def list_all_recommendations():
    """List all recommendations for user"""
    try:
        user_id = get_current_user_id()

        recommendations = LessonRecommendationEngine.generate_recommendations(user_id)
        
        return jsonify(recommendations), 200
        
    except Exception as e:
        logger.error(f"[Recommendations] Error listing: {e}")
        return jsonify({'error': str(e)}), 500
