"""Compatibility routes to match frontend AI endpoints.

These endpoints map older frontend expectations to the current backend implementations.
"""
from flask import Blueprint, request
from flask_jwt_extended import jwt_required
from . import ai_chat, ai_questions, ai_recommendations

bp = Blueprint('ai_compat', __name__)


@bp.route('/ask', methods=['POST'])
@jwt_required()
def ask():
    """Compatibility: POST /api/ai/ask -> ai_chat.chat_with_ai"""
    return ai_chat.chat_with_ai()


@bp.route('/generate', methods=['POST'])
@jwt_required()
def generate():
    """Compatibility: POST /api/ai/generate -> ai_questions.generate_questions"""
    return ai_questions.generate_questions()


@bp.route('/recommendations', methods=['GET'])
@jwt_required()
def recommendations():
    """Compatibility: GET /api/ai/recommendations -> ai_recommendations.get_recommendations"""
    return ai_recommendations.get_recommendations()


@bp.route('/<int:recommendation_id>/view', methods=['POST'])
@jwt_required()
def mark_viewed(recommendation_id):
    """Compatibility: mark recommendation as viewed"""
    try:
        from models import db, AIRecommendation
        rec = AIRecommendation.query.get(recommendation_id)
        if not rec:
            return ({'error': 'Recommendation not found'}, 404)
        rec.is_viewed = True
        db.session.commit()
        return ({'message': 'Marked as viewed', 'recommendation_id': recommendation_id}, 200)
    except Exception as e:
        return ({'error': str(e)}, 500)
