"""
prep_photo.py

Prepares a source photo for ASCII conversion:
  1. Convert to grayscale
  2. Boost local contrast with CLAHE (contrast-limited adaptive histogram
     equalization) so a flatly-lit face gets real highlights/shadows
  3. Composite onto pure white so background maps to the blank end of
     the ASCII ramp (white -> spaces)

Note: if your source photo has a busy/non-white background, run it
through a background remover (e.g. rembg) before this step, or crop
tightly to the subject. This version assumes a clean/plain background,
which is the common case for headshots.

Usage:
    python scripts/prep_photo.py source-photo.png
Output:
    prepped.png
"""
import sys
import cv2
import numpy as np
from PIL import Image


def prep_photo(input_path: str, output_path: str = "prepped.png") -> None:
    img = Image.open(input_path).convert("RGB")
    gray = np.array(img.convert("L"))

    # CLAHE contrast boost -- this is what gives a flat face real
    # highlights and shadows instead of a muddy gray blob.
    clahe = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8))
    contrasted = clahe.apply(gray)

    # Lightly brighten the very light pixels toward pure white so a
    # near-white background collapses fully into the blank glyph.
    threshold = 235
    contrasted = np.where(contrasted >= threshold, 255, contrasted).astype(np.uint8)

    out = Image.fromarray(contrasted, mode="L")
    out.save(output_path)
    print(f"Wrote {output_path} ({out.size[0]}x{out.size[1]})")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python scripts/prep_photo.py <source-photo>")
        sys.exit(1)
    prep_photo(sys.argv[1])
