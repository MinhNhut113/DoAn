from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from utils import get_current_user_id
from models import db, Assignment, AssignmentSubmission, Lesson
from datetime import datetime

bp = Blueprint('assignments', __name__)

@bp.route('/lesson/<int:lesson_id>', methods=['GET'])
@jwt_required()
def get_assignment_for_lesson(lesson_id):
    """Get assignment details for a lesson and user's previous submission if any"""
    try:
        user_id = get_current_user_id()
        
        # Check if lesson exists and get course_id
        lesson = Lesson.query.get(lesson_id)
        if not lesson:
            return jsonify({'error': 'Lesson not found'}), 404
        
        # Get assignment for this lesson
        assignment = Assignment.query.filter_by(lesson_id=lesson_id).first()
        
        if not assignment:
            return jsonify({'assignment': None}), 200
        
        # Get user's previous submission
        submission = AssignmentSubmission.query.filter_by(
            assignment_id=assignment.assignment_id,
            user_id=user_id
        ).first()
        
        response_data = {
            'assignment': assignment.to_dict(),
            'submission': submission.to_dict() if submission else None
        }
        
        return jsonify(response_data), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/submit', methods=['POST'])
@jwt_required()
def submit_assignment():
    """Create or update an assignment submission"""
    try:
        user_id = get_current_user_id()
        data = request.get_json() or {}
        
        assignment_id = data.get('assignment_id')
        submission_content = data.get('submission_content')
        file_url = data.get('file_url')
        
        if not assignment_id:
            return jsonify({'error': 'assignment_id is required'}), 400
        
        # Check if assignment exists
        assignment = Assignment.query.get(assignment_id)
        if not assignment:
            return jsonify({'error': 'Assignment not found'}), 404
        
        # Check if user already submitted
        submission = AssignmentSubmission.query.filter_by(
            assignment_id=assignment_id,
            user_id=user_id
        ).first()
        
        if submission:
            # Update existing submission
            submission.submission_content = submission_content
            submission.file_url = file_url
            submission.submitted_at = datetime.utcnow()
            # Clear grading if re-submitted
            submission.score = None
            submission.feedback = None
            submission.graded_at = None
        else:
            # Create new submission
            submission = AssignmentSubmission(
                assignment_id=assignment_id,
                user_id=user_id,
                submission_content=submission_content,
                file_url=file_url,
                submitted_at=datetime.utcnow()
            )
            db.session.add(submission)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Assignment submitted successfully',
            'submission': submission.to_dict()
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500
