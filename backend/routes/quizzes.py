from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required
from utils import get_current_user_id
from models import db, Quiz, QuizQuestion, QuizResult, QuizAnswer, Topic, QuizQuestionMapping
import json

bp = Blueprint('quizzes', __name__)

@bp.route('', methods=['GET'])
@jwt_required()
def get_quizzes():
    try:
        course_id = request.args.get('course_id', type=int)
        topic_id = request.args.get('topic_id', type=int)
        
        query = Quiz.query
        if course_id:
            query = query.filter_by(course_id=course_id)
        if topic_id:
            query = query.filter_by(topic_id=topic_id)
        
        quizzes = query.all()
        return jsonify([quiz.to_dict() for quiz in quizzes]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:quiz_id>', methods=['GET'])
@jwt_required()
def get_quiz(quiz_id):
    try:
        quiz = Quiz.query.get(quiz_id)
        
        if not quiz:
            return jsonify({'error': 'Quiz not found'}), 404
        
        quiz_data = quiz.to_dict()
        
        # Get questions for this quiz
        mappings = QuizQuestionMapping.query.filter_by(quiz_id=quiz_id).order_by(QuizQuestionMapping.question_order).all()
        questions = []
        for mapping in mappings:
            question = QuizQuestion.query.get(mapping.question_id)
            if question:
                questions.append(question.to_dict(include_answer=False))
        
        quiz_data['questions'] = questions
        
        return jsonify(quiz_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/<int:quiz_id>/submit', methods=['POST'])
@jwt_required()
def submit_quiz(quiz_id):
    try:
        user_id = get_current_user_id()
        quiz = Quiz.query.get(quiz_id)
        
        if not quiz:
            return jsonify({'error': 'Quiz not found'}), 404
        
        data = request.get_json()
        answers = data.get('answers', [])  # [{question_id: 1, selected_answer: 2}, ...]
        time_taken_minutes = data.get('time_taken_minutes', 0)
        
        # Get questions
        mappings = QuizQuestionMapping.query.filter_by(quiz_id=quiz_id).all()
        question_ids = [m.question_id for m in mappings]
        questions = {q.question_id: q for q in QuizQuestion.query.filter(QuizQuestion.question_id.in_(question_ids)).all()}

        total_questions = len(questions)
        correct_count = 0
        answer_details = []

        for answer_data in answers:
            question_id = answer_data.get('question_id')
            selected_answer = answer_data.get('selected_answer')
            time_spent = answer_data.get('time_spent_seconds', 0)

            if question_id not in questions:
                continue

            question = questions[question_id]
            is_correct = (selected_answer == question.correct_answer)

            if is_correct:
                correct_count += 1

            answer_details.append({
                'question_id': question_id,
                'selected_answer': selected_answer,
                'is_correct': is_correct,
                'correct_answer': question.correct_answer,
                'explanation': question.explanation,
                'time_spent_seconds': time_spent
            })
        
        score = (correct_count / total_questions * 100) if total_questions > 0 else 0
        
        # Save quiz result
        result = QuizResult(
            user_id=user_id,
            quiz_id=quiz_id,
            score=score,
            total_questions=total_questions,
            correct_answers=correct_count,
            time_taken_minutes=time_taken_minutes
        )
        db.session.add(result)
        db.session.flush()
        
        # Save individual answers
        for answer_data in answers:
            question_id = answer_data.get('question_id')
            if question_id in questions_dict:
                question = questions_dict[question_id]
                quiz_answer = QuizAnswer(
                    result_id=result.result_id,
                    question_id=question_id,
                    selected_answer=answer_data.get('selected_answer'),
                    is_correct=(answer_data.get('selected_answer') == question.correct_answer),
                    time_spent_seconds=answer_data.get('time_spent_seconds', 0)
                )
                db.session.add(quiz_answer)
        
        db.session.commit()
        
        return jsonify({
            'message': 'Quiz submitted successfully',
            'result': {
                'result_id': result.result_id,
                'score': float(score),
                'total_questions': total_questions,
                'correct_answers': correct_count,
                'passed': score >= quiz.passing_score,
                'answers': answer_details
            }
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/results', methods=['GET'])
@jwt_required()
def get_quiz_results():
    try:
        user_id = get_current_user_id()
        quiz_id = request.args.get('quiz_id', type=int)
        
        query = QuizResult.query.filter_by(user_id=user_id)
        if quiz_id:
            query = query.filter_by(quiz_id=quiz_id)
        
        results = query.order_by(QuizResult.submitted_at.desc()).all()
        return jsonify([result.to_dict() for result in results]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@bp.route('/questions', methods=['GET'])
@jwt_required()
def get_questions():
    try:
        course_id = request.args.get('course_id', type=int)
        topic_id = request.args.get('topic_id', type=int)
        
        query = QuizQuestion.query
        if course_id:
            query = query.filter_by(course_id=course_id)
        if topic_id:
            query = query.filter_by(topic_id=topic_id)
        
        questions = query.all()
        return jsonify([q.to_dict(include_answer=False) for q in questions]), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

