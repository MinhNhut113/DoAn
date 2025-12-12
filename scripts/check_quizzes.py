#!/usr/bin/env python3
"""Check what quizzes exist in the database"""
from backend.models import db, Quiz
from backend import app

with app.app_context():
    quizzes = Quiz.query.all()
    print(f"Found {len(quizzes)} quizzes:")
    for quiz in quizzes:
        print(f"ID: {quiz.quiz_id}, Name: {quiz.quiz_name}, Course: {quiz.course_id}")

    # Check for lesson quizzes
    lesson_quizzes = Quiz.query.filter(Quiz.quiz_name.like('LessonQuiz:%')).all()
    print(f"\nFound {len(lesson_quizzes)} lesson quizzes:")
    for quiz in lesson_quizzes:
        print(f"ID: {quiz.quiz_id}, Name: {quiz.quiz_name}")