"""
Image generator for synthetic image data.

Generates placeholder and synthetic image data for testing
and development purposes.
"""

from dataclasses import dataclass, field
from typing import Optional, Any, List, Tuple
from enum import Enum
import io
import base64
from pathlib import Path

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PIL = True
except ImportError:
    HAS_PIL = False

import numpy as np
import pandas as pd


class ImageFormat(str, Enum):
    """Supported image formats."""

    PNG = "png"
    JPEG = "jpeg"
    GIF = "gif"
    BMP = "bmp"
    WEBP = "webp"
    BASE64 = "base64"  # Base64 encoded string


class ImageType(str, Enum):
    """Types of images to generate."""

    SOLID = "solid"  # Solid color
    GRADIENT = "gradient"  # Gradient color
    PATTERN = "pattern"  # Geometric pattern
    PLACEHOLDER = "placeholder"  # Placeholder with text
    NOISE = "noise"  # Random noise
    PHOTO = "photo"  # Photo-like (simulated)
    BARCODE = "barcode"  # Barcode
    QR = "qr"  # QR code


@dataclass
class ImagePattern:
    """Pattern for image generation."""

    field_name: str
    image_type: ImageType
    width: int = 100
    height: int = 100
    format: ImageFormat = ImageFormat.PNG

    # Color parameters
    primary_color: Optional[Tuple[int, int, int]] = None  # RGB
    secondary_color: Optional[Tuple[int, int, int]] = None

    # Text for placeholder images
    text: Optional[str] = None

    # Noise parameters
    noise_level: float = 0.5

    # Quality (for JPEG)
    quality: int = 85


class ImageGenerator:
    """
    Generate synthetic images.

    Creates placeholder images for testing purposes.
    Supports various image types and formats.
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize generator.

        Args:
            seed: Random seed
        """
        self.seed = seed
        if seed is not None:
            np.random.seed(seed)

        if not HAS_PIL:
            import warnings
            warnings.warn(
                "PIL/Pillow not available. Image generation will be limited. "
                "Install with: pip install Pillow"
            )

    def generate(
        self,
        pattern: ImagePattern,
        count: int,
    ) -> list[str]:
        """
        Generate images based on pattern.

        Args:
            pattern: Image pattern
            count: Number of images to generate

        Returns:
            List of image data (base64 encoded strings or file paths)
        """
        if not HAS_PIL:
            # Return placeholder strings
            return [self._generate_placeholder_string(pattern, i) for i in range(count)]

        results = []

        for i in range(count):
            image = self._generate_single_image(pattern, i)
            encoded = self._encode_image(image, pattern.format)
            results.append(encoded)

        return results

    def _generate_single_image(
        self,
        pattern: ImagePattern,
        index: int,
    ) -> Image.Image:
        """Generate a single image."""
        # Create image
        img = Image.new('RGB', (pattern.width, pattern.height), color='white')
        draw = ImageDraw.Draw(img)

        if pattern.image_type == ImageType.SOLID:
            self._draw_solid(draw, img, pattern)

        elif pattern.image_type == ImageType.GRADIENT:
            self._draw_gradient(img, pattern)

        elif pattern.image_type == ImageType.PATTERN:
            self._draw_pattern(draw, pattern)

        elif pattern.image_type == ImageType.PLACEHOLDER:
            self._draw_placeholder(draw, img, pattern, index)

        elif pattern.image_type == ImageType.NOISE:
            self._draw_noise(img, pattern)

        elif pattern.image_type == ImageType.BARCODE:
            self._draw_barcode(draw, img, pattern, index)

        elif pattern.image_type == ImageType.QR:
            self._draw_qr(draw, img, pattern, index)

        return img

    def _draw_solid(self, draw: ImageDraw.Draw, img: Image.Image, pattern: ImagePattern):
        """Draw solid color image."""
        color = pattern.primary_color or (128, 128, 128)
        draw.rectangle([0, 0, pattern.width, pattern.height], fill=color)

    def _draw_gradient(self, img: Image.Image, pattern: ImagePattern):
        """Draw gradient image."""
        color1 = pattern.primary_color or (0, 0, 0)
        color2 = pattern.secondary_color or (255, 255, 255)

        # Create simple vertical gradient
        for y in range(pattern.height):
            ratio = y / pattern.height
            r = int(color1[0] * (1 - ratio) + color2[0] * ratio)
            g = int(color1[1] * (1 - ratio) + color2[1] * ratio)
            b = int(color1[2] * (1 - ratio) + color2[2] * ratio)
            for x in range(pattern.width):
                img.putpixel((x, y), (r, g, b))

    def _draw_pattern(self, draw: ImageDraw.Draw, pattern: ImagePattern):
        """Draw geometric pattern."""
        color = pattern.primary_color or (0, 0, 0)

        # Draw checkerboard pattern
        square_size = max(10, min(pattern.width, pattern.height) // 10)
        for y in range(0, pattern.height, square_size):
            for x in range(0, pattern.width, square_size):
                if ((x // square_size) + (y // square_size)) % 2 == 0:
                    draw.rectangle(
                        [x, y, x + square_size, y + square_size],
                        fill=color
                    )

    def _draw_placeholder(
        self,
        draw: ImageDraw.Draw,
        img: Image.Image,
        pattern: ImagePattern,
        index: int,
    ):
        """Draw placeholder with text."""
        # Background
        bg_color = pattern.primary_color or (200, 200, 200)
        draw.rectangle([0, 0, pattern.width, pattern.height], fill=bg_color)

        # Border
        border_color = pattern.secondary_color or (100, 100, 100)
        draw.rectangle(
            [0, 0, pattern.width - 1, pattern.height - 1],
            outline=border_color,
            width=2
        )

        # Text
        text = pattern.text or f"{pattern.width}x{pattern.height}"
        if index > 0:
            text = f"{text}_{index}"

        # Try to use a font
        try:
            font_size = max(12, min(pattern.width, pattern.height) // 10)
            font = ImageFont.truetype("arial.ttf", font_size)
        except:
            font = ImageFont.load_default()

        # Calculate text position (centered)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]

        x = (pattern.width - text_width) // 2
        y = (pattern.height - text_height) // 2

        text_color = (0, 0, 0)
        draw.text((x, y), text, fill=text_color, font=font)

    def _draw_noise(self, img: Image.Image, pattern: ImagePattern):
        """Draw random noise."""
        noise = np.random.randint(0, 256, (pattern.height, pattern.width, 3), dtype=np.uint8)

        # Apply noise level
        if pattern.noise_level < 1.0:
            base = np.array(img)
            noise = (noise * pattern.noise_level + base * (1 - pattern.noise_level)).astype(np.uint8)

        # Put pixels
        for y in range(pattern.height):
            for x in range(pattern.width):
                img.putpixel((x, y), tuple(noise[y, x]))

    def _draw_barcode(
        self,
        draw: ImageDraw.Draw,
        img: Image.Image,
        pattern: ImagePattern,
        index: int,
    ):
        """Draw simple barcode."""
        # Background
        draw.rectangle([0, 0, pattern.width, pattern.height], fill='white')

        # Barcode parameters
        bar_color = pattern.primary_color or (0, 0, 0)
        bar_width = max(2, pattern.width // 50)
        margin = bar_width * 2

        # Generate pseudo-random barcode pattern
        np.random.seed(index or self.seed or 0)
        x = margin
        while x < pattern.width - margin:
            # Bar width varies
            w = bar_width * np.random.randint(1, 4)
            if x + w > pattern.width - margin:
                w = pattern.width - margin - x

            # Randomly draw bar or space
            if np.random.random() > 0.5:
                draw.rectangle([x, margin, x + w, pattern.height - margin], fill=bar_color)

            x += w + bar_width

    def _draw_qr(
        self,
        draw: ImageDraw.Draw,
        img: Image.Image,
        pattern: ImagePattern,
        index: int,
    ):
        """Draw simple QR-like pattern."""
        # Background
        draw.rectangle([0, 0, pattern.width, pattern.height], fill='white')

        # QR module size
        module_size = max(4, min(pattern.width, pattern.height) // 25)

        # Create pseudo-random QR pattern
        np.random.seed(index or self.seed or 0)
        modules = pattern.width // module_size

        color = pattern.primary_color or (0, 0, 0)

        for y in range(modules):
            for x in range(modules):
                if np.random.random() > 0.5:
                    draw.rectangle(
                        [
                            x * module_size,
                            y * module_size,
                            (x + 1) * module_size - 1,
                            (y + 1) * module_size - 1
                        ],
                        fill=color
                    )

        # Add position markers (corners)
        marker_size = 7 * module_size
        for corner_x, corner_y in [(0, 0), (pattern.width - marker_size, 0), (0, pattern.height - marker_size)]:
            # Outer square
            draw.rectangle(
                [corner_x, corner_y, corner_x + marker_size, corner_y + marker_size],
                outline=color,
                width=module_size
            )
            # Inner square
            inner_size = 3 * module_size
            offset = 2 * module_size
            draw.rectangle(
                [corner_x + offset, corner_y + offset,
                 corner_x + offset + inner_size, corner_y + offset + inner_size],
                fill=color
            )

    def _encode_image(self, image: Image.Image, format: ImageFormat) -> str:
        """Encode image to base64 string."""
        buffer = io.BytesIO()

        # Determine format and save
        if format == ImageFormat.JPEG:
            image.save(buffer, format='JPEG', quality=85)
        elif format == ImageFormat.PNG:
            image.save(buffer, format='PNG')
        elif format == ImageFormat.GIF:
            image.save(buffer, format='GIF')
        elif format == ImageFormat.BMP:
            image.save(buffer, format='BMP')
        else:
            image.save(buffer, format='PNG')

        # Encode to base64
        buffer.seek(0)
        base64_bytes = base64.b64encode(buffer.read())
        base64_string = base64_bytes.decode('utf-8')

        return base64_string

    def _generate_placeholder_string(self, pattern: ImagePattern, index: int) -> str:
        """Generate placeholder string when PIL is not available."""
        return f"data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

    def save_to_file(
        self,
        image_data: str,
        file_path: str,
    ) -> None:
        """
        Save image data to file.

        Args:
            image_data: Base64 encoded image data
            file_path: Output file path
        """
        # Decode base64
        image_bytes = base64.b64decode(image_data)

        # Write to file
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'wb') as f:
            f.write(image_bytes)


class ImagePatternAnalyzer:
    """
    Analyze image data to learn patterns.

    Extracts statistics from image datasets for generation.
    """

    def __init__(self):
        """Initialize analyzer."""
        pass

    def analyze(
        self,
        images: List[Any],
        field_name: str,
    ) -> ImagePattern:
        """
        Analyze image data.

        Args:
            images: List of image data (file paths or base64)
            field_name: Field name

        Returns:
            ImagePattern for generation
        """
        if not images:
            return ImagePattern(
                field_name=field_name,
                image_type=ImageType.PLACEHOLDER,
                width=100,
                height=100,
            )

        # Analyze first image as sample
        sample = images[0]

        if isinstance(sample, str) and sample.startswith('data:image'):
            # Base64 encoded
            return ImagePattern(
                field_name=field_name,
                image_type=ImageType.PLACEHOLDER,
                width=100,
                height=100,
                format=ImageFormat.BASE64,
            )

        # Try to get image dimensions
        if HAS_PIL:
            try:
                if isinstance(sample, str) and Path(sample).exists():
                    img = Image.open(sample)
                else:
                    # Assume base64
                    img_bytes = base64.b64decode(sample)
                    img = Image.open(io.BytesIO(img_bytes))

                return ImagePattern(
                    field_name=field_name,
                    image_type=ImageType.NOISE,
                    width=img.width,
                    height=img.height,
                )
            except:
                pass

        # Default pattern
        return ImagePattern(
            field_name=field_name,
            image_type=ImageType.PLACEHOLDER,
            width=100,
            height=100,
        )


# Convenience functions
def generate_placeholder_images(
    field_name: str,
    count: int,
    width: int = 100,
    height: int = 100,
    seed: Optional[int] = None,
) -> list[str]:
    """
    Generate placeholder images.

    Args:
        field_name: Name of the field
        count: Number of images
        width: Image width
        height: Image height
        seed: Random seed

    Returns:
        List of base64 encoded images
    """
    pattern = ImagePattern(
        field_name=field_name,
        image_type=ImageType.PLACEHOLDER,
        width=width,
        height=height,
        text=f"{width}x{height}",
    )

    generator = ImageGenerator(seed=seed)
    return generator.generate(pattern, count)
