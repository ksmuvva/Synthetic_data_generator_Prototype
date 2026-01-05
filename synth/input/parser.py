"""
Input file parser for multiple formats.

Program of Thoughts:
1. Detect file format from extension
2. Parse file into DataFrame
3. Handle encoding issues
4. Extract metadata
5. Support: CSV, Excel, JSON, PDF
"""

from pathlib import Path
from typing import Optional, Union
import pandas as pd
import chardet

from synth.core.errors import InputError, FileFormatError


class FileParser:
    """
    Parse various file formats into DataFrame.

    Self-Reflection:
    1. Is format detection accurate?
    2. Are encoding issues handled?
    3. Are errors informative?
    """

    SUPPORTED_FORMATS = {
        ".csv": "csv",
        ".xlsx": "excel",
        ".xls": "excel",
        ".xlsm": "excel",
        ".json": "json",
        ".jsonl": "jsonl",
        ".parquet": "parquet",
        ".feather": "feather",
        ".pkl": "pickle",
        ".pdf": "pdf",
        ".txt": "text",
        ".tsv": "csv",  # Tab-separated
    }

    def __init__(self, encoding: str = "utf-8", sample_size: int = 10000):
        """
        Initialize file parser.

        Args:
            encoding: Default encoding for text files
            sample_size: Sample size for format detection
        """
        self.encoding = encoding
        self.sample_size = sample_size

    def parse(
        self,
        file_path: Union[str, Path],
        format_type: Optional[str] = None,
        **kwargs
    ) -> pd.DataFrame:
        """
        Parse file into DataFrame.

        PoT Steps:
        1. Validate file exists
        2. Detect format (if not provided)
        3. Call appropriate parser
        4. Validate output
        5. Return DataFrame

        Args:
            file_path: Path to file
            format_type: Force specific format
            **kwargs: Additional arguments for parser

        Returns:
            Parsed DataFrame

        Raises:
            InputError: If file cannot be parsed
        """
        file_path = Path(file_path)

        # Validate file exists
        if not file_path.exists():
            raise InputError(f"File not found: {file_path}")

        # Detect format
        if format_type is None:
            format_type = self._detect_format(file_path)

        # Parse based on format
        if format_type == "csv":
            df = self._parse_csv(file_path, **kwargs)
        elif format_type == "excel":
            df = self._parse_excel(file_path, **kwargs)
        elif format_type == "json":
            df = self._parse_json(file_path, **kwargs)
        elif format_type == "jsonl":
            df = self._parse_jsonl(file_path, **kwargs)
        elif format_type == "parquet":
            df = self._parse_parquet(file_path, **kwargs)
        elif format_type == "pdf":
            df = self._parse_pdf(file_path, **kwargs)
        elif format_type == "text":
            df = self._parse_text(file_path, **kwargs)
        else:
            raise FileFormatError(
                format_type,
                list(self.SUPPORTED_FORMATS.values())
            )

        # Validate output
        if df.empty:
            raise InputError(f"Empty DataFrame parsed from {file_path}")

        return df

    def _detect_format(self, file_path: Path) -> str:
        """Detect file format from extension."""
        suffix = file_path.suffix.lower()

        if suffix not in self.SUPPORTED_FORMATS:
            raise FileFormatError(
                suffix,
                list(self.SUPPORTED_FORMATS.keys())
            )

        return self.SUPPORTED_FORMATS[suffix]

    def _detect_encoding(self, file_path: Path) -> str:
        """Detect file encoding using chardet."""
        try:
            with open(file_path, "rb") as f:
                raw_data = f.read(10000)  # Read first 10KB
                result = chardet.detect(raw_data)
                return result["encoding"] or self.encoding
        except Exception:
            return self.encoding

    def _parse_csv(
        self,
        file_path: Path,
        encoding: Optional[str] = None,
        delimiter: Optional[str] = None,
        **kwargs
    ) -> pd.DataFrame:
        """
        Parse CSV file.

        PoT:
        1. Detect encoding if not provided
        2. Detect delimiter if not provided
        3. Handle quoting
        4. Parse with pandas
        """
        # Detect encoding
        if encoding is None:
            encoding = self._detect_encoding(file_path)

        # Detect delimiter
        if delimiter is None:
            delimiter = self._detect_delimiter(file_path, encoding)

        # Default kwargs
        default_kwargs = {
            "encoding": encoding,
            "sep": delimiter,
            "low_memory": False,
            "on_bad_lines": "warn",
        }
        default_kwargs.update(kwargs)

        try:
            return pd.read_csv(file_path, **default_kwargs)
        except Exception as e:
            raise InputError(f"Failed to parse CSV: {str(e)}")

    def _detect_delimiter(self, file_path: Path, encoding: str) -> str:
        """Detect CSV delimiter."""
        try:
            with open(file_path, "r", encoding=encoding) as f:
                sample = f.read(1024)

            # Count common delimiters
            delimiters = {
                ",": sample.count(","),
                ";": sample.count(";"),
                "\t": sample.count("\t"),
                "|": sample.count("|"),
            }

            # Return most common (excluding newlines)
            delimiters["\n"] = 0
            return max(delimiters, key=delimiters.get)
        except Exception:
            return ","  # Default to comma

    def _parse_excel(
        self,
        file_path: Path,
        sheet_name: Union[str, int, list] = 0,
        **kwargs
    ) -> pd.DataFrame:
        """
        Parse Excel file.

        PoT:
        1. Handle multiple sheets
        2. Preserve formulas if possible
        3. Handle merged cells
        """
        default_kwargs = {
            "sheet_name": sheet_name,
            "engine": "openpyxl",
        }
        default_kwargs.update(kwargs)

        try:
            df = pd.read_excel(file_path, **default_kwargs)
            return df
        except Exception as e:
            raise InputError(f"Failed to parse Excel file: {str(e)}")

    def _parse_json(
        self,
        file_path: Path,
        orient: str = "records",
        **kwargs
    ) -> pd.DataFrame:
        """Parse JSON file."""
        default_kwargs = {"orient": orient}
        default_kwargs.update(kwargs)

        try:
            return pd.read_json(file_path, **default_kwargs)
        except Exception as e:
            raise InputError(f"Failed to parse JSON: {str(e)}")

    def _parse_jsonl(
        self,
        file_path: Path,
        lines: bool = True,
        **kwargs
    ) -> pd.DataFrame:
        """Parse JSON Lines file."""
        default_kwargs = {"lines": lines}
        default_kwargs.update(kwargs)

        try:
            return pd.read_json(file_path, **default_kwargs)
        except Exception as e:
            raise InputError(f"Failed to parse JSONL: {str(e)}")

    def _parse_parquet(
        self,
        file_path: Path,
        **kwargs
    ) -> pd.DataFrame:
        """Parse Parquet file."""
        try:
            return pd.read_parquet(file_path, **kwargs)
        except Exception as e:
            raise InputError(f"Failed to parse Parquet: {str(e)}")

    def _parse_pdf(
        self,
        file_path: Path,
        **kwargs
    ) -> pd.DataFrame:
        """
        Parse PDF file (extract tables).

        PoT:
        1. Use pdfplumber or camelot
        2. Extract all tables
        3. Combine into single DataFrame
        """
        try:
            import pdfplumber
        except ImportError:
            raise InputError(
                "PDF parsing requires pdfplumber. "
                "Install with: pip install pdfplumber"
            )

        try:
            tables = []
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_tables = page.extract_tables()
                    for table in page_tables:
                        if table:
                            # Convert to DataFrame
                            df = pd.DataFrame(table[1:], columns=table[0])
                            tables.append(df)

            if not tables:
                raise InputError(f"No tables found in PDF: {file_path}")

            # Combine all tables
            if len(tables) == 1:
                return tables[0]
            else:
                return pd.concat(tables, ignore_index=True)

        except Exception as e:
            raise InputError(f"Failed to parse PDF: {str(e)}")

    def _parse_text(
        self,
        file_path: Path,
        **kwargs
    ) -> pd.DataFrame:
        """Parse text file (one record per line)."""
        try:
            # Try to parse as JSON lines first
            return self._parse_jsonl(file_path, **kwargs)
        except Exception:
            # Fall back to simple text reading
            try:
                with open(file_path, "r", encoding=self.encoding) as f:
                    lines = f.readlines()

                return pd.DataFrame({"text": lines})
            except Exception as e:
                raise InputError(f"Failed to parse text file: {str(e)}")


def create_sample_csv(output_path: Path, rows: int = 100) -> Path:
    """
    Create a sample CSV file for testing.

    Args:
        output_path: Where to save the file
        rows: Number of rows to generate

    Returns:
        Path to created file
    """
    import numpy as np

    np.random.seed(42)

    df = pd.DataFrame({
        "customer_id": [f"CUST-{i:08d}" for i in range(rows)],
        "name": [f"Customer_{i}" for i in range(rows)],
        "age": np.random.randint(18, 80, rows),
        "email": [f"customer{i}@example.com" for i in range(rows)],
        "salary": np.random.normal(75000, 25000, rows).astype(int),
        "department": np.random.choice(["Engineering", "Sales", "HR", "Marketing"], rows),
        "join_date": pd.date_range("2020-01-01", periods=rows, freq="D"),
        "is_active": np.random.choice([True, False], rows),
    })

    df.to_csv(output_path, index=False)
    return output_path
