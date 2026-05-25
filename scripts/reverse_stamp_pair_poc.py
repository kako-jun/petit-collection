#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np

from reverse_stamp_poc import (
    auto_levels,
    center_crop,
    ensure_dir,
    label_tile,
    load_image,
    red_dominance_mask,
    select_stamp_component,
)


def ordered_box_points(mask: np.ndarray) -> np.ndarray:
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        raise ValueError("failed to find contour for stamp component")
    contour = max(contours, key=cv2.contourArea)
    rect = cv2.minAreaRect(contour)
    box = cv2.boxPoints(rect).astype(np.float32)
    sums = box.sum(axis=1)
    diffs = np.diff(box, axis=1).reshape(-1)
    top_left = box[np.argmin(sums)]
    bottom_right = box[np.argmax(sums)]
    top_right = box[np.argmin(diffs)]
    bottom_left = box[np.argmax(diffs)]
    return np.array([top_left, top_right, bottom_right, bottom_left], dtype=np.float32)


def compute_red_strength(image: np.ndarray, mask: np.ndarray) -> np.ndarray:
    blue, green, red = cv2.split(image)
    strength = (
        red.astype(np.int16) - ((green.astype(np.int16) + blue.astype(np.int16)) // 2)
    ).clip(0, 255).astype(np.uint8)
    strength = cv2.bitwise_and(strength, mask)
    strength = auto_levels(strength)
    return cv2.createCLAHE(clipLimit=2.5, tileGridSize=(8, 8)).apply(strength)


def warp_stamp(path: Path, crop_ratio: float, size: int) -> dict[str, np.ndarray]:
    image = center_crop(load_image(path), crop_ratio)
    base_mask = red_dominance_mask(image)
    stamp_mask = select_stamp_component(base_mask)
    source = ordered_box_points(stamp_mask)
    target = np.array(
        [[0, 0], [size - 1, 0], [size - 1, size - 1], [0, size - 1]],
        dtype=np.float32,
    )
    transform = cv2.getPerspectiveTransform(source, target)
    warped = cv2.warpPerspective(image, transform, (size, size))
    warped_mask = cv2.warpPerspective(stamp_mask, transform, (size, size))
    warped_mask = ((warped_mask > 127).astype(np.uint8)) * 255
    red_strength = compute_red_strength(warped, warped_mask)
    isolated = np.where(warped_mask[:, :, None] > 0, warped, np.full_like(warped, 245))
    return {
        "warped": warped,
        "mask": warped_mask,
        "red_strength": red_strength,
        "isolated": isolated,
    }


def colorize_mask(mask: np.ndarray, ink_bgr: tuple[int, int, int]) -> np.ndarray:
    soft = cv2.GaussianBlur(mask, (0, 0), 1.1)
    alpha = (soft.astype(np.float32) / 255.0)[:, :, None]
    paper = np.full((mask.shape[0], mask.shape[1], 3), 245, dtype=np.float32)
    ink = np.full((mask.shape[0], mask.shape[1], 3), ink_bgr, dtype=np.float32)
    return np.clip(paper * (1.0 - alpha) + ink * alpha, 0, 255).astype(np.uint8)


def colorize_heatmap(gray: np.ndarray) -> np.ndarray:
    normalized = auto_levels(gray)
    return cv2.applyColorMap(normalized, cv2.COLORMAP_INFERNO)


def build_contact_sheet(variants: dict[str, np.ndarray], columns: int = 3) -> np.ndarray:
    tiles = [label_tile(name, image) for name, image in variants.items()]
    rows = (len(tiles) + columns - 1) // columns
    blank = np.full_like(tiles[0], 248)
    tiles.extend([blank] * (rows * columns - len(tiles)))
    return np.vstack(
        [np.hstack(tiles[row * columns : (row + 1) * columns]) for row in range(rows)]
    )


def write_gallery(output_dir: Path, stem: str) -> None:
    html = f"""<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <title>petit-collection reverse stamp pair POC</title>
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
      .card {{
        background: #fffaf2;
        border: 1px solid #d7c8af;
        border-radius: 16px;
        padding: 16px;
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
      <h1>Reverse-side multi-view proof of concept</h1>
      <p>
        The key comparison is between the top-down red-strength map and the oblique red-strength map.
        Areas that weaken in the oblique view are candidates for recessed or partially hidden structure.
      </p>
      <section class="card">
        <img src="{stem}/_contact_sheet.png" alt="pair contact sheet" />
      </section>
    </main>
  </body>
</html>
"""
    (output_dir / "_gallery.html").write_text(html, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare top-down and oblique reverse-side stamp photos."
    )
    parser.add_argument("top_view", type=Path, help="Top-down reverse-side stamp photo")
    parser.add_argument("oblique_view", type=Path, help="Oblique reverse-side stamp photo")
    parser.add_argument(
        "--reference",
        type=Path,
        help="Optional front/reference photo to include for comparison",
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("output/reverse-stamp-pair-poc"),
        help="Directory where the comparison set will be written",
    )
    parser.add_argument(
        "--crop-ratio",
        type=float,
        default=0.7,
        help="Center crop ratio before processing (default: 0.7)",
    )
    parser.add_argument(
        "--size",
        type=int,
        default=1024,
        help="Square output size after perspective normalization (default: 1024)",
    )
    parser.add_argument(
        "--difference-threshold",
        type=int,
        default=28,
        help="Threshold for meaningful red-strength change between views (default: 28)",
    )
    args = parser.parse_args()

    top = warp_stamp(args.top_view, args.crop_ratio, args.size)
    oblique = warp_stamp(args.oblique_view, args.crop_ratio, args.size)
    common_mask = cv2.bitwise_and(top["mask"], oblique["mask"])

    difference = cv2.absdiff(top["red_strength"], oblique["red_strength"])
    difference = cv2.bitwise_and(difference, common_mask)

    hidden_when_oblique = cv2.subtract(top["red_strength"], oblique["red_strength"])
    hidden_when_oblique = cv2.bitwise_and(hidden_when_oblique, common_mask)
    hidden_mask = cv2.threshold(
        hidden_when_oblique, args.difference_threshold, 255, cv2.THRESH_BINARY
    )[1]
    hidden_mask = cv2.morphologyEx(hidden_mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

    gained_when_oblique = cv2.subtract(oblique["red_strength"], top["red_strength"])
    gained_when_oblique = cv2.bitwise_and(gained_when_oblique, common_mask)
    gained_mask = cv2.threshold(
        gained_when_oblique, args.difference_threshold, 255, cv2.THRESH_BINARY
    )[1]
    gained_mask = cv2.morphologyEx(gained_mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

    hidden_overlay = top["isolated"].copy()
    hidden_overlay[hidden_mask > 0] = (210, 40, 20)
    hidden_overlay = cv2.addWeighted(top["isolated"], 0.55, hidden_overlay, 0.45, 0)

    variants: dict[str, np.ndarray] = {
        "01_top_isolated": top["isolated"],
        "02_oblique_isolated": oblique["isolated"],
        "03_top_red_strength": cv2.cvtColor(top["red_strength"], cv2.COLOR_GRAY2BGR),
        "04_oblique_red_strength": cv2.cvtColor(oblique["red_strength"], cv2.COLOR_GRAY2BGR),
        "05_common_mask": cv2.cvtColor(common_mask, cv2.COLOR_GRAY2BGR),
        "06_abs_difference": colorize_heatmap(difference),
        "07_hidden_when_oblique_gray": cv2.cvtColor(hidden_when_oblique, cv2.COLOR_GRAY2BGR),
        "08_hidden_when_oblique_mask": cv2.cvtColor(hidden_mask, cv2.COLOR_GRAY2BGR),
        "09_hidden_when_oblique_blue": colorize_mask(hidden_mask, (150, 45, 35)),
        "10_gained_when_oblique_mask": cv2.cvtColor(gained_mask, cv2.COLOR_GRAY2BGR),
        "11_hidden_overlay": hidden_overlay,
    }

    if args.reference is not None:
        reference = warp_stamp(args.reference, args.crop_ratio, args.size)
        variants["12_reference_isolated"] = reference["isolated"]
        variants["13_reference_red_strength"] = cv2.cvtColor(
            reference["red_strength"], cv2.COLOR_GRAY2BGR
        )

    stem = f"{args.top_view.stem}__{args.oblique_view.stem}"
    pair_dir = args.output_dir / stem
    ensure_dir(pair_dir)
    for name, image in variants.items():
        cv2.imwrite(str(pair_dir / f"{name}.png"), image)
    cv2.imwrite(str(pair_dir / "_contact_sheet.png"), build_contact_sheet(variants))
    write_gallery(args.output_dir, stem)


if __name__ == "__main__":
    main()
