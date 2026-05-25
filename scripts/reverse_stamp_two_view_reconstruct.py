#!/usr/bin/env python3

from __future__ import annotations

import argparse
from pathlib import Path

import cv2
import numpy as np

from reverse_stamp_pair_poc import build_contact_sheet, warp_stamp, write_gallery
from reverse_stamp_poc import ensure_dir


def pseudo_ink(mask: np.ndarray, ink_bgr: tuple[int, int, int]) -> np.ndarray:
    soft = cv2.GaussianBlur(mask, (0, 0), 1.0)
    alpha = (soft.astype(np.float32) / 255.0)[:, :, None]
    paper = np.full((mask.shape[0], mask.shape[1], 3), 245, dtype=np.float32)
    ink = np.full((mask.shape[0], mask.shape[1], 3), ink_bgr, dtype=np.float32)
    return np.clip(paper * (1.0 - alpha) + ink * alpha, 0, 255).astype(np.uint8)


def keep_large_components(mask: np.ndarray, min_area: int) -> np.ndarray:
    count, labels, stats, _ = cv2.connectedComponentsWithStats(mask)
    kept = np.zeros_like(mask)
    for label in range(1, count):
        area = stats[label, cv2.CC_STAT_AREA]
        if area >= min_area:
            kept[labels == label] = 255
    return kept


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Reconstruct a pseudo stamped image from top + oblique reverse-side photos."
    )
    parser.add_argument("top_view", type=Path)
    parser.add_argument("oblique_view", type=Path)
    parser.add_argument("--reference", type=Path)
    parser.add_argument(
        "-o",
        "--output-dir",
        type=Path,
        default=Path("output/reverse-stamp-two-view-reconstruct"),
    )
    parser.add_argument("--crop-ratio", type=float, default=0.7)
    parser.add_argument("--size", type=int, default=1024)
    parser.add_argument(
        "--fill-threshold",
        type=int,
        default=138,
        help="Stable red-strength threshold for filled raised areas.",
    )
    parser.add_argument(
        "--line-low",
        type=int,
        default=42,
        help="Low Canny threshold for outline extraction.",
    )
    parser.add_argument(
        "--line-high",
        type=int,
        default=108,
        help="High Canny threshold for outline extraction.",
    )
    args = parser.parse_args()

    top = warp_stamp(args.top_view, args.crop_ratio, args.size)
    oblique = warp_stamp(args.oblique_view, args.crop_ratio, args.size)
    common_mask = cv2.bitwise_and(top["mask"], oblique["mask"])

    top_strength = top["red_strength"]
    oblique_strength = oblique["red_strength"]
    stable_strength = np.minimum(top_strength, oblique_strength)
    stable_strength = cv2.bitwise_and(stable_strength, common_mask)

    # Top view is the final geometry. Oblique view is only a visibility test:
    # if a region stays similarly strong from both views, it is likely part of the raised top surface.
    top_f = top_strength.astype(np.float32)
    oblique_f = oblique_strength.astype(np.float32)
    visibility_ratio = np.divide(
        oblique_f + 1.0,
        top_f + 1.0,
        out=np.zeros_like(top_f),
        where=top_f > 0,
    )
    visibility_ratio = np.clip(visibility_ratio, 0.0, 1.25)
    visible_surface = (
        (top_strength >= args.fill_threshold)
        & (visibility_ratio >= 0.72)
        & (common_mask > 0)
    ).astype(np.uint8) * 255

    fill_candidate = visible_surface
    fill_candidate = cv2.morphologyEx(
        fill_candidate, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8)
    )
    fill_candidate = cv2.morphologyEx(
        fill_candidate, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8)
    )
    fill_candidate = keep_large_components(fill_candidate, min_area=140)

    # Outlines should also follow the top-view geometry, but only where the oblique view
    # did not substantially hide the ridge.
    smooth = cv2.GaussianBlur(top_strength, (0, 0), 1.2)
    line_candidate = cv2.Canny(smooth, args.line_low, args.line_high)
    line_visibility = (
        (top_strength >= max(args.line_low // 2, 20))
        & (visibility_ratio >= 0.58)
        & (common_mask > 0)
    ).astype(np.uint8) * 255
    line_candidate = cv2.bitwise_and(line_candidate, line_visibility)
    line_candidate = cv2.dilate(line_candidate, np.ones((2, 2), np.uint8), iterations=1)
    line_candidate = cv2.morphologyEx(
        line_candidate, cv2.MORPH_OPEN, np.ones((2, 2), np.uint8)
    )

    combined = cv2.bitwise_or(fill_candidate, line_candidate)
    combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, np.ones((3, 3), np.uint8))
    combined = cv2.bitwise_and(combined, common_mask)

    fill_blue = pseudo_ink(fill_candidate, (150, 45, 35))
    fill_red = pseudo_ink(fill_candidate, (60, 60, 190))
    combined_blue = pseudo_ink(combined, (150, 45, 35))
    combined_red = pseudo_ink(combined, (60, 60, 190))

    overlay = top["isolated"].copy()
    overlay[fill_candidate > 0] = (215, 70, 30)
    overlay[line_candidate > 0] = (250, 220, 70)
    overlay = cv2.addWeighted(top["isolated"], 0.56, overlay, 0.44, 0)

    variants: dict[str, np.ndarray] = {
        "01_top_isolated": top["isolated"],
        "02_oblique_isolated": oblique["isolated"],
        "03_top_red_strength": cv2.cvtColor(top_strength, cv2.COLOR_GRAY2BGR),
        "04_oblique_red_strength": cv2.cvtColor(oblique_strength, cv2.COLOR_GRAY2BGR),
        "05_stable_strength": cv2.cvtColor(stable_strength, cv2.COLOR_GRAY2BGR),
        "06_visibility_ratio": cv2.applyColorMap(
            (visibility_ratio * 255.0 / 1.25).astype(np.uint8), cv2.COLORMAP_VIRIDIS
        ),
        "07_fill_candidate_mask": cv2.cvtColor(fill_candidate, cv2.COLOR_GRAY2BGR),
        "08_line_candidate_mask": cv2.cvtColor(line_candidate, cv2.COLOR_GRAY2BGR),
        "09_combined_mask": cv2.cvtColor(combined, cv2.COLOR_GRAY2BGR),
        "10_fill_blue": fill_blue,
        "11_fill_red": fill_red,
        "12_combined_blue": combined_blue,
        "13_combined_red": combined_red,
        "14_debug_overlay": overlay,
    }

    if args.reference is not None:
        reference = warp_stamp(args.reference, args.crop_ratio, args.size)
        variants["15_reference_isolated"] = reference["isolated"]
        variants["16_reference_red_strength"] = cv2.cvtColor(
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
