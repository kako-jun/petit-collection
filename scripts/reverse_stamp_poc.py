#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def load_image(path: Path) -> np.ndarray:
    image = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"failed to read image: {path}")
    return image


def center_crop(image: np.ndarray, crop_ratio: float) -> np.ndarray:
    if not 0.1 <= crop_ratio <= 1.0:
        raise ValueError("crop_ratio must be between 0.1 and 1.0")
    height, width = image.shape[:2]
    cropped_h = int(height * crop_ratio)
    cropped_w = int(width * crop_ratio)
    top = max((height - cropped_h) // 2, 0)
    left = max((width - cropped_w) // 2, 0)
    return image[top : top + cropped_h, left : left + cropped_w]


def auto_levels(gray: np.ndarray) -> np.ndarray:
    return cv2.normalize(gray, None, 0, 255, cv2.NORM_MINMAX)


def make_pseudo_stamp_variants(image: np.ndarray) -> dict[str, np.ndarray]:
    flipped = cv2.flip(image, 1)
    gray = cv2.cvtColor(flipped, cv2.COLOR_BGR2GRAY)
    leveled = auto_levels(gray)

    blur = cv2.GaussianBlur(leveled, (0, 0), 1.4)
    detail = cv2.addWeighted(leveled, 1.8, blur, -0.8, 0)

    binary = cv2.adaptiveThreshold(
        detail,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        61,
        6,
    )
    binary_inv = 255 - binary

    kernel = np.ones((3, 3), np.uint8)
    opened = cv2.morphologyEx(binary_inv, cv2.MORPH_OPEN, kernel)
    closed = cv2.morphologyEx(opened, cv2.MORPH_CLOSE, kernel)

    ink_mask = closed
    soft_mask = cv2.GaussianBlur(ink_mask, (0, 0), 1.2)
    paper = np.full_like(flipped, 245)
    ink = np.zeros_like(flipped)
    ink[:, :, 0] = 35
    ink[:, :, 1] = 45
    ink[:, :, 2] = 150

    alpha = (soft_mask.astype(np.float32) / 255.0)[:, :, None]
    pseudo_blue = np.clip(paper * (1.0 - alpha) + ink * alpha, 0, 255).astype(np.uint8)

    red_ink = np.zeros_like(flipped)
    red_ink[:, :, 0] = 35
    red_ink[:, :, 1] = 35
    red_ink[:, :, 2] = 185
    pseudo_red = np.clip(paper * (1.0 - alpha) + red_ink * alpha, 0, 255).astype(np.uint8)

    overlay = cv2.cvtColor(detail, cv2.COLOR_GRAY2BGR)
    edges = cv2.Canny(detail, 80, 160)
    overlay[edges > 0] = (0, 0, 255)

    return {
        "01_flipped": flipped,
        "02_gray_levels": cv2.cvtColor(leveled, cv2.COLOR_GRAY2BGR),
        "03_detail": cv2.cvtColor(detail, cv2.COLOR_GRAY2BGR),
        "04_binary_mask": cv2.cvtColor(binary_inv, cv2.COLOR_GRAY2BGR),
        "05_clean_mask": cv2.cvtColor(ink_mask, cv2.COLOR_GRAY2BGR),
        "06_pseudo_blue": pseudo_blue,
        "07_pseudo_red": pseudo_red,
        "08_edge_overlay": overlay,
    }


def save_variants(source_path: Path, variants: dict[str, np.ndarray], output_dir: Path) -> None:
    stem_dir = output_dir / source_path.stem
    ensure_dir(stem_dir)
    for name, image in variants.items():
        out_path = stem_dir / f"{name}.png"
        cv2.imwrite(str(out_path), image)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate pseudo-stamp variants from reverse-side pre-ink photos."
    )
    parser.add_argument("inputs", nargs="+", type=Path, help="Input image files")
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("output/reverse-stamp-poc"),
        help="Directory where variants will be written",
    )
    parser.add_argument(
        "--crop-ratio",
        type=float,
        default=0.7,
        help="Center crop ratio before processing (default: 0.7)",
    )
    args = parser.parse_args()

    ensure_dir(args.output_dir)
    for input_path in args.inputs:
        image = load_image(input_path)
        cropped = center_crop(image, args.crop_ratio)
        variants = make_pseudo_stamp_variants(cropped)
        save_variants(input_path, variants, args.output_dir)


if __name__ == "__main__":
    main()
