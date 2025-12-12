#!/usr/bin/env python3
"""Test frontend logic for recommendations"""
import json

# Simulate the API response
api_response = {
    "recommendations": [
        {
            "course_id": 2,
            "lesson_id": 2,
            "lesson_title": "Xây Dựng Nền Móng Web: HTML Cơ Bản Cho Người Mới Bắt Đầu",
            "priority": 2,
            "reason": "Bạn chưa bắt đầu bài học này. Hãy hoàn thành để tiến bộ.",
            "type": "incomplete_lesson"
        },
        {
            "course_id": 2,
            "lesson_id": 3,
            "lesson_title": "CSS Cơ Bản: Tạo Style Cho Trang Web",
            "priority": 2,
            "reason": "Bạn chưa bắt đầu bài học này. Hãy hoàn thành để tiến bộ.",
            "type": "incomplete_lesson"
        }
    ],
    "total_recommendations": 2
}

# Test the frontend logic
def test_frontend_logic():
    response = api_response  # This is what aiAPI.getRecommendations returns
    recommendations = response.get('recommendations', [])  # This is the fix

    print(f"✅ Got {len(recommendations)} recommendations")

    if recommendations:
        # Test slicing
        sliced = recommendations[:5]  # slice(0, 5) equivalent
        print(f"✅ Sliced to {len(sliced)} items")

        # Test mapping
        html_parts = []
        for rec in sliced:
            html = f"""
                    <div style="padding: 1rem; margin-bottom: 1rem; background: var(--light-color); border-radius: 5px;">
                        <strong>{rec.get('lesson_title', 'Nội dung được đề xuất')}</strong>
                        <p style="margin-top: 0.5rem; color: #6b7280;">{rec.get('reason', '')}</p>
                        <a href="lesson.html?id={rec.get('lesson_id', '')}" class="btn btn-primary" style="margin-top: 0.5rem;">Xem Bài Học</a>
                    </div>
                """
            html_parts.append(html.strip())

        final_html = ''.join(html_parts)
        print("✅ HTML generation successful")
        print("Sample HTML:")
        print(final_html[:200] + "...")

if __name__ == '__main__':
    test_frontend_logic()