"""
Multi-format output generators for synthetic data.

Provides generators for CSV, Excel, JSON, PDF, and Word formats.
"""

from synth.output.base import OutputGenerator, get_generator
from synth.output.csv import CSVGenerator
from synth.output.excel import ExcelGenerator
from synth.output.json import JSONGenerator
from synth.output.pdf import PDFGenerator
from synth.output.word import WordGenerator

__all__ = [
    "OutputGenerator",
    "get_generator",
    "CSVGenerator",
    "ExcelGenerator",
    "JSONGenerator",
    "PDFGenerator",
    "WordGenerator",
]
