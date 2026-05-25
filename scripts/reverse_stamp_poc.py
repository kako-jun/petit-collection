#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

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


def red_dominance_mask(image: np.ndarray) -> np.ndarray:
    blue, green, red = cv2.split(image)
    red16 = red.astype(np.int16)
    green16 = green.astype(np.int16)
    blue16 = blue.astype(np.int16)
    mask = (
        (red > 110)
        & (red16 > green16 + 35)
        & (red16 > blue16 + 35)
    ).astype(np.uint8) * 255
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((5, 5), np.uint8))
    return mask


def select_stamp_component(mask: np.ndarray) -> np.ndarray:
    count, labels, stats, centroids = cv2.connectedComponentsWithStats(mask)
    height, width = mask.shape
    center = np.array([width / 2.0, height / 2.0], dtype=np.float32)
    best_label = -1
    best_score = -1.0
    min_area = max(int(height * width * 0.005), 10_000)

    for label in range(1, count):
        x, y, component_w, component_h, area = stats[label]
        if area < min_area:
            continue
        aspect = min(component_w, component_h) / max(component_w, component_h)
        if aspect < 0.4:
            continue
        centroid = np.array(centroids[label], dtype=np.float32)
        dist = np.linalg.norm((centroid - center) / np.array([width, height], dtype=np.float32))
        score = float(area) * (aspect**3) / (0.2 + dist)
        if score > best_score:
            best_label = label
            best_score = score

    if best_label == -1:
        raise ValueError("failed to isolate the stamp surface from the image")

    component = (labels == best_label).astype(np.uint8) * 255
    component = cv2.morphologyEx(component, cv2.MORPH_CLOSE, np.ones((11, 11), np.uint8))
    return component


def select_stamp_circle_mask(component_mask: np.ndarray) -> np.ndarray:
    distance = cv2.distanceTransform(component_mask, cv2.DIST_L2, 5)
    _, max_value, _, max_loc = cv2.minMaxLoc(distance)
    if max_value <= 0:
        raise ValueError("failed to estimate stamp circle center")

    contours, _ = cv2.findContours(component_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if not contours:
        raise ValueError("failed to estimate stamp circle contour")
    contour = max(contours, key=cv2.contourArea).reshape(-1, 2).astype(np.float32)

    center = np.array(max_loc, dtype=np.float32)
    distances = np.linalg.norm(contour - center[None, :], axis=1)
    lower = np.percentile(distances, 35)
    upper = np.percentile(distances, 85)
    circle_band = distances[(distances >= lower) & (distances <= upper)]
    radius = float(np.median(circle_band)) if circle_band.size else float(np.median(distances))
    radius = max(radius, float(max_value) * 1.12)

    circle_mask = np.zeros_like(component_mask)
    cv2.circle(
        circle_mask,
        (int(round(center[0])), int(round(center[1]))),
        int(round(radius)),
        255,
        thickness=-1,
    )
    circle_mask = cv2.bitwise_and(circle_mask, component_mask)
    circle_mask = cv2.morphologyEx(circle_mask, cv2.MORPH_CLOSE, np.ones((9, 9), np.uint8))
    return circle_mask


def crop_to_mask(
    image: np.ndarray, mask: np.ndarray, pad_ratio: float = 0.08
) -> tuple[np.ndarray, np.ndarray]:
    ys, xs = np.where(mask > 0)
    if len(xs) == 0 or len(ys) == 0:
        raise ValueError("mask is empty")

    min_x, max_x = xs.min(), xs.max()
    min_y, max_y = ys.min(), ys.max()
    width = max_x - min_x + 1
    height = max_y - min_y + 1
    pad = int(max(width, height) * pad_ratio)

    left = max(min_x - pad, 0)
    top = max(min_y - pad, 0)
    right = min(max_x + pad + 1, image.shape[1])
    bottom = min(max_y + pad + 1, image.shape[0])
    return image[top:bottom, left:right], mask[top:bottom, left:right]


def whiten_background(image: np.ndarray, mask: np.ndarray, paper_value: int = 245) -> np.ndarray:
    white = np.full_like(image, paper_value)
    return np.where(mask[:, :, None] > 0, image, white)


def pseudo_ink(mask: np.ndarray, ink_bgr: tuple[int, int, int], paper_value: int = 245) -> np.ndarray:
    soft_mask = cv2.GaussianBlur(mask, (0, 0), 1.1)
    alpha = (soft_mask.astype(np.float32) / 255.0)[:, :, None]
    paper = np.full((mask.shape[0], mask.shape[1], 3), paper_value, dtype=np.float32)
    ink = np.full((mask.shape[0], mask.shape[1], 3), ink_bgr, dtype=np.float32)
    return np.clip(paper * (1.0 - alpha) + ink * alpha, 0, 255).astype(np.uint8)


def debug_overlay(source: np.ndarray, mask: np.ndarray) -> np.ndarray:
    overlay = source.copy()
    overlay[mask > 0] = (20, 40, 210)
    return cv2.addWeighted(source, 0.55, overlay, 0.45, 0)


def label_tile(label: str, image: np.ndarray, tile_size: int = 420) -> np.ndarray:
    if image.ndim == 2:
        image = cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)
    canvas = np.full((tile_size, tile_size, 3), 248, dtype=np.uint8)
    label_h = 44
    avail_h = tile_size - label_h - 24
    avail_w = tile_size - 24
    scale = min(avail_w / image.shape[1], avail_h / image.shape[0])
    resized = cv2.resize(
        image,
        (max(1, int(image.shape[1] * scale)), max(1, int(image.shape[0] * scale))),
        interpolation=cv2.INTER_AREA,
    )
    y = label_h + 12 + (avail_h - resized.shape[0]) // 2
    x = 12 + (avail_w - resized.shape[1]) // 2
    canvas[y : y + resized.shape[0], x : x + resized.shape[1]] = resized
    cv2.putText(
        canvas,
        label,
        (18, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.75,
        (30, 30, 30),
        2,
        cv2.LINE_AA,
    )
    return canvas


def make_contact_sheet(variants: dict[str, np.ndarray], columns: int = 3) -> np.ndarray:
    tiles = [label_tile(name, image) for name, image in variants.items()]
    rows = (len(tiles) + columns - 1) // columns
    blank = np.full_like(tiles[0], 248)
    padded_tiles = tiles + [blank] * (rows * columns - len(tiles))
    row_images = []
    for row in range(rows):
        start = row * columns
        row_images.append(np.hstack(padded_tiles[start : start + columns]))
    return np.vstack(row_images)


def make_pseudo_stamp_variants(image: np.ndarray) -> dict[str, np.ndarray]:
    base_mask = red_dominance_mask(image)
    stamp_mask = select_stamp_component(base_mask)
    cropped, cropped_mask = crop_to_mask(image, stamp_mask)

    flipped = cv2.flip(cropped, 1)
    flipped_mask = cv2.flip(cropped_mask, 1)
    isolated = whiten_background(flipped, flipped_mask)

    blue, green, red = cv2.split(flipped)
    red_strength = (
        red.astype(np.int16) - ((green.astype(np.int16) + blue.astype(np.int16)) // 2)
    ).clip(0, 255).astype(np.uint8)
    red_strength = cv2.bitwise_and(red_strength, flipped_mask)
    red_strength = auto_levels(red_strength)
    red_strength = cv2.GaussianBlur(red_strength, (0, 0), 1.0)
    leveled = cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(red_strength)

    fill_mask = cv2.adaptiveThreshold(
        leveled,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        51,
        -4,
    )
    fill_mask = cv2.bitwise_and(fill_mask, flipped_mask)
    fill_mask = cv2.morphologyEx(fill_mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    fill_mask = cv2.morphologyEx(fill_mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))

    blackhat = cv2.morphologyEx(leveled, cv2.MORPH_BLACKHAT, np.ones((9, 9), np.uint8))
    groove_mask = cv2.threshold(blackhat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    groove_mask = cv2.bitwise_and(groove_mask, flipped_mask)
    groove_mask = cv2.morphologyEx(groove_mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

    groove_inverted = cv2.bitwise_and(cv2.bitwise_not(groove_mask), flipped_mask)
    groove_inverted = cv2.morphologyEx(groove_inverted, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))

    fill_blue = pseudo_ink(fill_mask, (150, 45, 35))
    fill_red = pseudo_ink(fill_mask, (60, 60, 190))
    relief_blue = pseudo_ink(groove_inverted, (150, 45, 35))
    relief_red = pseudo_ink(groove_inverted, (60, 60, 190))

    return {
        "01_source_flipped": flipped,
        "02_stamp_isolated": isolated,
        "03_stamp_mask": cv2.cvtColor(flipped_mask, cv2.COLOR_GRAY2BGR),
        "04_red_strength": cv2.cvtColor(leveled, cv2.COLOR_GRAY2BGR),
        "05_fill_mask": cv2.cvtColor(fill_mask, cv2.COLOR_GRAY2BGR),
        "06_groove_inverse_mask": cv2.cvtColor(groove_inverted, cv2.COLOR_GRAY2BGR),
        "07_pseudo_blue_fill": fill_blue,
        "08_pseudo_red_fill": fill_red,
        "09_pseudo_blue_relief": relief_blue,
        "10_pseudo_red_relief": relief_red,
        "11_debug_overlay": debug_overlay(isolated, fill_mask),
    }


def save_variants(source_path: Path, variants: dict[str, np.ndarray], output_dir: Path) -> None:
    stem_dir = output_dir / source_path.stem
    ensure_dir(stem_dir)
    for name, image in variants.items():
        out_path = stem_dir / f"{name}.png"
        cv2.imwrite(str(out_path), image)
    contact_sheet = make_contact_sheet(variants)
    cv2.imwrite(str(stem_dir / "_contact_sheet.png"), contact_sheet)


def write_gallery(output_dir: Path, source_names: Iterable[str]) -> None:
    cards = []
    for source_name in source_names:
        contact_rel = f"{source_name}/_contact_sheet.png"
        cards.append(
            f"""
            <section class="card">
              <h2>{source_name}</h2>
              <img src="{contact_rel}" alt="{source_name} contact sheet" />
            </section>
            """
        )
    html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>petit-collection reverse stamp POC</title>
    <style>
      body {{
        margin: 0;
        background: #efe9dc;
        color: #2d2116;
        font-family: sans-serif;
      }}
      main {{
        max-width: 1200px;
        margin: 0 auto;
        padding: 24px;
      }}
      h1 {{
        margin-bottom: 8px;
      }}
      p {{
        max-width: 72ch;
      }}
      .card {{
        background: #fffaf2;
        border: 1px solid #d7c8af;
        border-radius: 16px;
        padding: 16px;
        margin-top: 20px;
        box-shadow: 0 12px 32px rgba(90, 63, 26, 0.08);
      }}
      img {{
        width: 100%;
        height: auto;
        display: block;
        border-radius: 10px;
      }}
    </style>
  </head>
  <body>
    <main>
      <h1>Reverse-side stamp proof of concept</h1>
      <p>
        Variants compare two directions: a fill-first interpretation of raised red areas,
        and a groove-inverted interpretation that treats recessed shadows as paper.
      </p>
      {''.join(cards)}
    </main>
  </body>
</html>
"""
    (output_dir / "_gallery.html").write_text(html, encoding="utf-8")


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
    processed = []
    for input_path in args.inputs:
        image = load_image(input_path)
        cropped = center_crop(image, args.crop_ratio)
        variants = make_pseudo_stamp_variants(cropped)
        save_variants(input_path, variants, args.output_dir)
        processed.append(input_path.stem)
    write_gallery(args.output_dir, processed)


if __name__ == "__main__":
    main()
