#!/usr/bin/env python3
"""Check what lessons exist in the database"""
from backend.models import db, Lesson
from backend import app

with app.app_context():
    lessons = Lesson.query.all()
    print(f"Found {len(lessons)} lessons:")
    for lesson in lessons:
        print(f"ID: {lesson.lesson_id}, Title: {lesson.lesson_title}, Course: {lesson.course_id}")

    # Check if lesson 1003 exists
    lesson_1003 = Lesson.query.get(1003)
    if lesson_1003:
        print(f"\nLesson 1003 exists: {lesson_1003.lesson_title}")
    else:
        print("\nLesson 1003 does NOT exist")