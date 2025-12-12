import os
# Expose backend/ai_models directory as part of this package so imports like
# `from ai_models.ai_service import ...` resolve when project root is on PYTHONPATH.
__path__.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'backend', 'ai_models')))
