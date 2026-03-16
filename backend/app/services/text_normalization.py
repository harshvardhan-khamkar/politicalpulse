"""
Shared text normalization helpers for multilingual social content.
"""

from typing import Optional


def repair_mojibake(text: Optional[str]) -> str:
    """
    Recover text that was incorrectly stored via CP437 decoding of UTF-8 bytes.

    This pattern commonly shows up on Windows when UTF-8 text passes through a
    terminal or toolchain that assumes CP437.
    """
    if not text:
        return ""

    if any("\u0900" <= char <= "\u097F" for char in text):
        return text

    has_corruption = any(
        ("\u0391" <= char <= "\u03C9") or ("\u2500" <= char <= "\u25FF")
        for char in text
    )
    if not has_corruption:
        return text

    try:
        repaired = text.encode("cp437", errors="ignore").decode("utf-8", errors="ignore")
    except Exception:
        return text

    return repaired if any("\u0900" <= char <= "\u097F" for char in repaired) else text
