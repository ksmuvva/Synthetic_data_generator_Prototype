"""
PDF output generator using reportlab.

Generates professional PDF documents with tables and metadata.
"""

from pathlib import Path
from typing import Optional, Any
import pandas as pd
from datetime import datetime

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4, landscape
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import (
        SimpleDocTemplate,
        Table,
        TableStyle,
        Paragraph,
        Spacer,
        PageBreak,
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

from synth.output.base import OutputGenerator, GeneratorRegistry
from synth.patterns.schema import Schema


class PDFGenerator(OutputGenerator):
    """Generate PDF output files with tables and formatting."""

    def __init__(self, pagesize: str = "letter", orientation: str = "portrait"):
        """
        Initialize PDF generator.

        Args:
            pagesize: Page size ('letter' or 'a4')
            orientation: 'portrait' or 'landscape'
        """
        if not REPORTLAB_AVAILABLE:
            raise ImportError(
                "reportlab is required for PDF generation. "
                "Install it with: pip install reportlab"
            )

        # Set page size
        base_size = letter if pagesize.lower() == "letter" else A4
        if orientation.lower() == "landscape":
            self.pagesize = landscape(base_size)
        else:
            self.pagesize = base_size

        self.styles = getSampleStyleSheet()
        self._add_custom_styles()

    def _add_custom_styles(self) -> None:
        """Add custom paragraph styles."""
        self.styles.add(ParagraphStyle(
            name="CustomTitle",
            parent=self.styles["Heading1"],
            fontSize=18,
            textColor=colors.HexColor("#2c3e50"),
            spaceAfter=20,
            alignment=TA_CENTER,
        ))

        self.styles.add(ParagraphStyle(
            name="Metadata",
            parent=self.styles["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#7f8c8d"),
            leftIndent=20,
        ))

    def generate(
        self,
        data: pd.DataFrame,
        output_path: Path,
        schema: Optional[Schema] = None,
        title: str = "Synthetic Data",
        include_metadata: bool = True,
        max_rows_per_page: int = 30,
        **kwargs
    ) -> Path:
        """
        Generate PDF file with data table.

        Args:
            data: DataFrame to write
            output_path: Where to save the PDF
            schema: Optional schema for metadata
            title: Document title
            include_metadata: Include schema metadata if available
            max_rows_per_page: Maximum rows per table page
            **kwargs: Additional options

        Returns:
            Path to the generated PDF file
        """
        # Ensure output path has .pdf extension
        output_path = Path(output_path)
        if output_path.suffix != ".pdf":
            output_path = output_path.with_suffix(".pdf")

        # Create parent directory if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create PDF document
        doc = SimpleDocTemplate(
            str(output_path),
            pagesize=self.pagesize,
            rightMargin=0.5 * inch,
            leftMargin=0.5 * inch,
            topMargin=0.5 * inch,
            bottomMargin=0.5 * inch,
        )

        # Build content
        story = []

        # Add title
        title_para = Paragraph(title, self.styles["CustomTitle"])
        story.append(title_para)
        story.append(Spacer(1, 0.2 * inch))

        # Add generation timestamp
        timestamp = Paragraph(
            f"<i>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</i>",
            self.styles["Metadata"]
        )
        story.append(timestamp)
        story.append(Spacer(1, 0.2 * inch))

        # Add metadata if schema provided
        if schema and include_metadata:
            story.extend(self._build_metadata_section(schema))
            story.append(Spacer(1, 0.2 * inch))

        # Add data table(s)
        story.extend(self._build_data_table(data, max_rows_per_page))

        # Add footer
        story.append(PageBreak())
        footer = Paragraph(
            f"<i>Total records: {len(data)}</i>",
            self.styles["Metadata"]
        )
        story.append(footer)

        # Build PDF
        doc.build(story)

        return output_path

    def _build_metadata_section(self, schema: Schema) -> list:
        """Build metadata section from schema."""
        items = [
            f"<b>Row Count:</b> {schema.row_count}",
            f"<b>Fields:</b> {len(schema.fields)}",
        ]

        # Add field info
        for field in schema.fields[:5]:  # Show first 5 fields
            items.append(f"<b>{field.name}:</b> {field.type.value}")
            if field.unique:
                items.append(f"  <i>Unique: Yes</i>")

        if len(schema.fields) > 5:
            items.append(f"<i>... and {len(schema.fields) - 5} more fields</i>")

        return [
            Paragraph(item, self.styles["Metadata"])
            for item in items
        ]

    def _build_data_table(self, data: pd.DataFrame, max_rows: int) -> list:
        """Build data table(s) from DataFrame."""
        tables = []

        # Convert DataFrame to table data
        headers = [str(col) for col in data.columns]
        all_rows = data.values.tolist()

        # Split into multiple tables if needed
        for i in range(0, len(all_rows), max_rows):
            chunk = all_rows[i:i + max_rows]
            table_data = [headers] + [[str(val) for val in row] for row in chunk]

            # Create table
            table = Table(table_data, repeatRows=1)

            # Apply styling
            table.setStyle(self._get_table_style())

            tables.append(table)
            tables.append(Spacer(1, 0.1 * inch))

        return tables

    def _get_table_style(self) -> TableStyle:
        """Get table style."""
        return TableStyle([
            # Header row
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#34495e")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
            ("ALIGN", (0, 0), (-1, 0), "CENTER"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, 0), 11),
            ("BOTTOMPADDING", (0, 0), (-1, 0), 12),

            # Data rows
            ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#ecf0f1")),
            ("TEXTCOLOR", (0, 1), (-1, -1), colors.HexColor("#2c3e50")),
            ("ALIGN", (0, 1), (-1, -1), "LEFT"),
            ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
            ("FONTSIZE", (0, 1), (-1, -1), 9),
            ("TOPPADDING", (0, 1), (-1, -1), 8),
            ("BOTTOMPADDING", (0, 1), (-1, -1), 8),

            # Grid
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ])

    def supports_format(self, format_type: str) -> bool:
        """Check if format is supported."""
        return format_type.lower() in ("pdf",)


# Register the generator
if REPORTLAB_AVAILABLE:
    GeneratorRegistry.register("pdf", PDFGenerator)
