#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np

from reverse_stamp_pair_poc import compute_red_strength, ordered_box_points
from reverse_stamp_poc import (
    auto_levels,
    center_crop,
    ensure_dir,
    label_tile,
    load_image,
    red_dominance_mask,
    select_stamp_circle_mask,
    select_stamp_component,
)


def extract_stamp(image_path: Path, crop_ratio: float) -> dict[str, np.ndarray]:
    image = center_crop(load_image(image_path), crop_ratio)
    base_mask = red_dominance_mask(image)
    stamp_component = select_stamp_component(base_mask)
    stamp_mask = select_stamp_circle_mask(stamp_component)
    box = ordered_box_points(stamp_mask)
    isolated = np.where(stamp_mask[:, :, None] > 0, image, np.full_like(image, 245))
    strength = compute_red_strength(image, stamp_mask)
    return {
        "image": image,
        "component_mask": stamp_component,
        "mask": stamp_mask,
        "box": box,
        "isolated": isolated,
        "strength": strength,
    }


def extract_reference_stamp(image_path: Path, crop_ratio: float) -> dict[str, np.ndarray]:
    image = center_crop(load_image(image_path), crop_ratio)
    hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    sat_mask = cv2.inRange(hsv, (0, 10, 90), (179, 180, 255))
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    dark_mask = cv2.threshold(gray, 210, 255, cv2.THRESH_BINARY_INV)[1]
    base_mask = cv2.bitwise_and(sat_mask, dark_mask)
    base_mask = cv2.morphologyEx(base_mask, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    base_mask = cv2.morphologyEx(base_mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    stamp_component = select_stamp_component(base_mask)
    stamp_mask = select_stamp_circle_mask(stamp_component)
    box = ordered_box_points(stamp_mask)
    isolated = np.where(stamp_mask[:, :, None] > 0, image, np.full_like(image, 245))

    # For the printed reference, preserve low-saturation brown-red ink instead of requiring red dominance.
    bgr_strength = (
        gray.astype(np.int16).max() - gray.astype(np.int16)
    ).clip(0, 255).astype(np.uint8)
    bgr_strength = cv2.bitwise_and(auto_levels(bgr_strength), stamp_mask)
    strength = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8)).apply(bgr_strength)
    return {
        "image": image,
        "component_mask": stamp_component,
        "mask": stamp_mask,
        "box": box,
        "isolated": isolated,
        "strength": strength,
    }


def pseudo_ink(mask: np.ndarray, ink_bgr: tuple[int, int, int]) -> np.ndarray:
    soft = cv2.GaussianBlur(mask, (0, 0), 1.0)
    alpha = (soft.astype(np.float32) / 255.0)[:, :, None]
    paper = np.full((mask.shape[0], mask.shape[1], 3), 245, dtype=np.float32)
    ink = np.full((mask.shape[0], mask.shape[1], 3), ink_bgr, dtype=np.float32)
    return np.clip(paper * (1.0 - alpha) + ink * alpha, 0, 255).astype(np.uint8)


def overlay_mask(base: np.ndarray, mask: np.ndarray, color: tuple[int, int, int]) -> np.ndarray:
    overlay = base.copy()
    overlay[mask > 0] = color
    return cv2.addWeighted(base, 0.58, overlay, 0.42, 0)


def warp_u8(image: np.ndarray, transform: np.ndarray, size: tuple[int, int], nearest: bool = False) -> np.ndarray:
    interpolation = cv2.INTER_NEAREST if nearest else cv2.INTER_LINEAR
    return cv2.warpPerspective(image, transform, size, flags=interpolation)


def refine_rotation(
    projected_top_strength: np.ndarray,
    projected_top_mask: np.ndarray,
    oblique_strength: np.ndarray,
    oblique_mask: np.ndarray,
    center: tuple[float, float],
    degree_range: float = 8.0,
    degree_step: float = 0.5,
) -> tuple[np.ndarray, float]:
    best_angle = 0.0
    best_score = float("-inf")
    best_rotation = np.eye(3, dtype=np.float32)
    height, width = oblique_strength.shape
    size = (width, height)

    for angle in np.arange(-degree_range, degree_range + 0.001, degree_step, dtype=np.float32):
        rotation_2x3 = cv2.getRotationMatrix2D(center, float(angle), 1.0)
        rotation = np.vstack([rotation_2x3, [0.0, 0.0, 1.0]]).astype(np.float32)
        rotated_strength = warp_u8(projected_top_strength, rotation, size)
        rotated_mask = warp_u8(projected_top_mask, rotation, size, nearest=True)
        shared = cv2.bitwise_and(((rotated_mask > 127).astype(np.uint8) * 255), oblique_mask)
        shared_pixels = int((shared > 0).sum())
        if shared_pixels < 10_000:
            continue

        diff = cv2.absdiff(rotated_strength, oblique_strength)
        mean_diff = float(diff[shared > 0].mean())
        overlap_ratio = shared_pixels / max(int((oblique_mask > 0).sum()), 1)
        score = overlap_ratio * 255.0 - mean_diff
        if score > best_score:
            best_score = score
            best_angle = float(angle)
            best_rotation = rotation

    return best_rotation, best_angle


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
    <title>petit-collection projective visibility POC</title>
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
      <h1>Projective visibility proof of concept</h1>
      <p>
        The top view is projected into the oblique camera frame, compared there, and only the
        regions that remain visible from the oblique view are carried back to the top-view result.
      </p>
      <section class="card">
        <img src="{stem}/_contact_sheet.png" alt="projective visibility contact sheet" />
      </section>
    </main>
  </body>
</html>
"""
    (output_dir / "_gallery.html").write_text(html, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compare top and oblique reverse-side stamp photos in the oblique camera frame."
    )
    parser.add_argument("top_view", type=Path)
    parser.add_argument("oblique_view", type=Path)
    parser.add_argument("--reference", type=Path)
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("output/reverse-stamp-projective-visibility"),
    )
    parser.add_argument("--crop-ratio", type=float, default=0.7)
    parser.add_argument(
        "--visibility-threshold",
        type=int,
        default=34,
        help="Difference threshold in the oblique frame before a region is treated as hidden.",
    )
    parser.add_argument(
        "--stable-threshold",
        type=int,
        default=96,
        help="Minimum top-view strength before a region is considered plausible inked surface.",
    )
    args = parser.parse_args()

    top = extract_stamp(args.top_view, args.crop_ratio)
    oblique = extract_stamp(args.oblique_view, args.crop_ratio)

    top_to_oblique = cv2.getPerspectiveTransform(top["box"], oblique["box"])
    oblique_to_top = cv2.getPerspectiveTransform(oblique["box"], top["box"])

    size_oblique = (oblique["image"].shape[1], oblique["image"].shape[0])
    size_top = (top["image"].shape[1], top["image"].shape[0])

    projected_top_strength = warp_u8(
        top["strength"], top_to_oblique, size_oblique
    )
    projected_top_mask = warp_u8(
        top["mask"], top_to_oblique, size_oblique, nearest=True
    )
    projected_top_mask = ((projected_top_mask > 127).astype(np.uint8)) * 255

    oblique_center = tuple(oblique["box"].mean(axis=0))
    rotation_refine, best_angle = refine_rotation(
        projected_top_strength,
        projected_top_mask,
        oblique["strength"],
        oblique["mask"],
        oblique_center,
    )
    top_to_oblique_refined = rotation_refine @ top_to_oblique
    oblique_to_top_refined = np.linalg.inv(top_to_oblique_refined).astype(np.float32)

    projected_top_strength = warp_u8(top["strength"], top_to_oblique_refined, size_oblique)
    projected_top_mask = warp_u8(top["mask"], top_to_oblique_refined, size_oblique, nearest=True)
    projected_top_mask = ((projected_top_mask > 127).astype(np.uint8)) * 255

    shared_oblique = cv2.bitwise_and(projected_top_mask, oblique["mask"])
    visible_strength = cv2.min(projected_top_strength, oblique["strength"])
    visible_strength = cv2.bitwise_and(visible_strength, shared_oblique)

    hidden_in_oblique = cv2.subtract(projected_top_strength, oblique["strength"])
    hidden_in_oblique = cv2.bitwise_and(hidden_in_oblique, shared_oblique)
    hidden_mask = cv2.threshold(
        hidden_in_oblique, args.visibility_threshold, 255, cv2.THRESH_BINARY
    )[1]
    hidden_mask = cv2.morphologyEx(hidden_mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))

    visible_mask_oblique = cv2.bitwise_and(shared_oblique, cv2.bitwise_not(hidden_mask))
    visible_mask_oblique = cv2.threshold(
        visible_mask_oblique, 127, 255, cv2.THRESH_BINARY
    )[1]

    visible_mask_top = warp_u8(
        visible_mask_oblique, oblique_to_top_refined, size_top, nearest=True
    )
    visible_mask_top = ((visible_mask_top > 127).astype(np.uint8)) * 255
    visible_mask_top = cv2.bitwise_and(visible_mask_top, top["mask"])

    stable_top = cv2.threshold(top["strength"], args.stable_threshold, 255, cv2.THRESH_BINARY)[1]
    stable_top = cv2.bitwise_and(stable_top, top["mask"])
    stable_top = cv2.morphologyEx(stable_top, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))

    fill_candidate = cv2.bitwise_and(stable_top, visible_mask_top)
    fill_candidate = cv2.morphologyEx(fill_candidate, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    fill_candidate = cv2.morphologyEx(fill_candidate, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))

    line_top = cv2.Canny(cv2.GaussianBlur(top["strength"], (0, 0), 1.2), 40, 105)
    line_top = cv2.bitwise_and(line_top, visible_mask_top)
    line_top = cv2.dilate(line_top, np.ones((2, 2), np.uint8), iterations=1)

    combined = cv2.bitwise_or(fill_candidate, line_top)
    combined = cv2.bitwise_and(combined, top["mask"])

    fill_red = pseudo_ink(fill_candidate, (60, 60, 190))
    combined_red = pseudo_ink(combined, (60, 60, 190))

    projected_top_mask_overlay = overlay_mask(
        oblique["isolated"], projected_top_mask, (70, 160, 240)
    )
    oblique_shared_overlay = overlay_mask(
        projected_top_mask_overlay, shared_oblique, (40, 210, 80)
    )
    hidden_overlay_oblique = overlay_mask(oblique_shared_overlay, hidden_mask, (210, 60, 20))

    visible_top_overlay = overlay_mask(top["isolated"], visible_mask_top, (70, 160, 240))
    fill_top_overlay = overlay_mask(visible_top_overlay, fill_candidate, (210, 60, 20))
    result_overlay_top = overlay_mask(fill_top_overlay, line_top, (240, 220, 80))

    variants: dict[str, np.ndarray] = {
        "01_top_isolated": top["isolated"],
        "02_oblique_isolated": oblique["isolated"],
        "03_top_component_mask": cv2.cvtColor(top["component_mask"], cv2.COLOR_GRAY2BGR),
        "04_top_circle_mask": cv2.cvtColor(top["mask"], cv2.COLOR_GRAY2BGR),
        "05_oblique_component_mask": cv2.cvtColor(oblique["component_mask"], cv2.COLOR_GRAY2BGR),
        "06_oblique_circle_mask": cv2.cvtColor(oblique["mask"], cv2.COLOR_GRAY2BGR),
        "07_top_red_strength": cv2.cvtColor(top["strength"], cv2.COLOR_GRAY2BGR),
        "08_oblique_red_strength": cv2.cvtColor(oblique["strength"], cv2.COLOR_GRAY2BGR),
        "09_projected_top_in_oblique": cv2.cvtColor(projected_top_strength, cv2.COLOR_GRAY2BGR),
        "10_rotation_refined_overlay": cv2.putText(
            projected_top_mask_overlay.copy(),
            f"best angle {best_angle:+.1f} deg",
            (24, 42),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (20, 20, 20),
            2,
            cv2.LINE_AA,
        ),
        "11_oblique_shared_overlay": oblique_shared_overlay,
        "12_hidden_in_oblique_gray": cv2.cvtColor(hidden_in_oblique, cv2.COLOR_GRAY2BGR),
        "13_hidden_in_oblique_mask": cv2.cvtColor(hidden_mask, cv2.COLOR_GRAY2BGR),
        "14_visible_mask_top": cv2.cvtColor(visible_mask_top, cv2.COLOR_GRAY2BGR),
        "15_fill_candidate_mask": cv2.cvtColor(fill_candidate, cv2.COLOR_GRAY2BGR),
        "16_line_candidate_mask": cv2.cvtColor(line_top, cv2.COLOR_GRAY2BGR),
        "17_combined_mask": cv2.cvtColor(combined, cv2.COLOR_GRAY2BGR),
        "18_fill_red": fill_red,
        "19_combined_red": combined_red,
        "20_hidden_overlay_oblique": hidden_overlay_oblique,
        "21_result_overlay_top": result_overlay_top,
    }

    if args.reference is not None:
        reference = extract_reference_stamp(args.reference, args.crop_ratio)
        variants["22_reference_isolated"] = reference["isolated"]
        variants["23_reference_red_strength"] = cv2.cvtColor(
            reference["strength"], cv2.COLOR_GRAY2BGR
        )

    stem = f"{args.top_view.stem}__{args.oblique_view.stem}"
    target_dir = args.output_dir / stem
    ensure_dir(target_dir)
    for name, image in variants.items():
        cv2.imwrite(str(target_dir / f"{name}.png"), image)
    cv2.imwrite(str(target_dir / "_contact_sheet.png"), build_contact_sheet(variants))
    write_gallery(args.output_dir, stem)


if __name__ == "__main__":
    main()
