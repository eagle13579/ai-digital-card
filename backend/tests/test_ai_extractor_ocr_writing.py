"""Aggregated tests for AI modules: extractor, ocr, writing_assistant.

Imports and re-exports all test classes from the per-module test files so
that ``pytest tests/test_ai_extractor_ocr_writing.py`` still works.
"""
# pylint: disable=unused-import
from tests.test_ai_extractor import (           # noqa: F401
    TestAIExtractorExtractFields,
    TestAIExtractorDefaultLayout,
    TestAIExtractorPDF,
    TestAIExtractorAsync,
)
from tests.test_ai_ocr import (                 # noqa: F401
    TestOCRPreprocess,
    TestOCRContactInfo,
    TestOCRBusinessInfo,
    TestOCRScanCard,
)
from tests.test_ai_writing_assistant import (   # noqa: F401
    TestWritingAssistantBuildPrompt,
    TestWritingAssistantGenerate,
)
