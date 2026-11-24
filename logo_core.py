"""LogoDesigner の純粋なロジック（標準ライブラリのみ）。

仕様フォーマット: ``logodesigner.logo.v1``

このモジュールは入出力やネットワークを一切行わない。
検証・正規化・SVG 生成だけを担当する。
"""

from __future__ import annotations

import math
import re
from xml.sax.saxutils import escape

__all__ = ["LogoError", "FORMAT", "SHAPES", "STYLES", "LAYOUTS",
           "validate_spec", "initials", "build_svg"]

FORMAT = "logodesigner.logo.v1"

SHAPES = ("circle", "rounded-square", "hexagon", "shield", "triangle", "badge")
STYLES = ("monogram", "badge", "minimal", "geometric")
LAYOUTS = ("icon-top", "icon-left", "icon-only", "text-only")

DEFAULTS = {
    "format": FORMAT,
    "brand": "",
    "tagline": "",
    "shape": "circle",
    "style": "monogram",
    "primary": "#2563eb",
    "accent": "#f59e0b",
    "text_color": "#111827",
    "background": "#ffffff",
    "layout": "icon-top",
    "size": 512,
}

_HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")


class LogoError(ValueError):
    """仕様が不正な場合に送出されるエラー。"""


def _has_control_chars(value: str) -> bool:
    return any(ord(ch) < 0x20 or ord(ch) == 0x7F for ch in value)


def _require_str(data: dict, key: str, default: str | None = None) -> str:
    value = data.get(key, default)
    if not isinstance(value, str):
        raise LogoError(f"{key} は文字列である必要があります")
    return value


def _validate_hex(value: object, key: str) -> str:
    if not isinstance(value, str) or not _HEX_RE.match(value):
        raise LogoError(f"{key} は #RRGGBB 形式である必要があります: {value!r}")
    return value.lower()


def validate_spec(data) -> dict:
    """仕様 dict を検証し、正規化した dict を返す。

    欠けている任意項目は既定値で補う。未知のキーは無視する。
    """
    if not isinstance(data, dict):
        raise LogoError("仕様はオブジェクトである必要があります")

    # format: あれば一致していること。なければ補う。
    fmt = data.get("format", FORMAT)
    if not isinstance(fmt, str) or fmt != FORMAT:
        raise LogoError(f"format は {FORMAT} である必要があります")

    if "brand" not in data:
        raise LogoError("brand は必須です")
    brand = data["brand"]
    if not isinstance(brand, str):
        raise LogoError("brand は文字列である必要があります")
    brand = brand.strip()
    if not brand:
        raise LogoError("brand は空にできません")
    if len(brand) > 30:
        raise LogoError("brand は 30 文字以内である必要があります")
    if _has_control_chars(brand):
        raise LogoError("brand に制御文字を含めることはできません")

    tagline = _require_str(data, "tagline", "")
    if len(tagline) > 60:
        raise LogoError("tagline は 60 文字以内である必要があります")
    if _has_control_chars(tagline):
        raise LogoError("tagline に制御文字を含めることはできません")

    shape = _require_str(data, "shape", "circle")
    if shape not in SHAPES:
        raise LogoError(f"shape が不明です: {shape!r}")

    style = _require_str(data, "style", "monogram")
    if style not in STYLES:
        raise LogoError(f"style が不明です: {style!r}")

    layout = _require_str(data, "layout", "icon-top")
    if layout not in LAYOUTS:
        raise LogoError(f"layout が不明です: {layout!r}")

    primary = _validate_hex(data.get("primary", "#2563eb"), "primary")
    accent = _validate_hex(data.get("accent", "#f59e0b"), "accent")
    text_color = _validate_hex(data.get("text_color", "#111827"), "text_color")

    background = data.get("background", "#ffffff")
    if isinstance(background, str) and background.lower() == "transparent":
        background = "transparent"
    else:
        background = _validate_hex(background, "background")

    size = data.get("size", 512)
    # bool は int のサブクラスなので先に弾く。float の NaN / inf も弾く。
    if isinstance(size, bool) or not isinstance(size, int):
        raise LogoError("size は整数である必要があります")
    if size < 128 or size > 2048:
        raise LogoError("size は 128 から 2048 の範囲である必要があります")

    return {
        "format": FORMAT,
        "brand": brand,
        "tagline": tagline,
        "shape": shape,
        "style": style,
        "primary": primary,
        "accent": accent,
        "text_color": text_color,
        "background": background,
        "layout": layout,
        "size": size,
    }


def initials(brand: str) -> str:
    """ブランド名から 1〜2 文字のイニシャルを返す。

    複数語の場合は最初の 2 語の頭文字、1 語の場合は先頭 2 文字。
    日本語など ASCII 英字で始まらない場合は先頭 1 文字をそのまま返す。
    """
    if not isinstance(brand, str) or not brand.strip():
        raise LogoError("brand は空にできません")
    words = brand.strip().split()
    first = words[0][0]
    if not ("A" <= first <= "Z" or "a" <= first <= "z"):
        return first

    letters: list[str] = []
    if len(words) >= 2:
        for word in words[:2]:
            for ch in word:
                if ch.isascii() and ch.isalpha():
                    letters.append(ch.upper())
                    break
    else:
        for ch in words[0]:
            if ch.isascii() and ch.isalpha():
                letters.append(ch.upper())
            if len(letters) >= 2:
                break
    return "".join(letters) if letters else first.upper()


def _num(value: float) -> str:
    """SVG 用の数値を短く整形する（整数は整数のまま）。"""
    rounded = round(float(value), 2)
    if rounded == int(rounded):
        return str(int(rounded))
    return f"{rounded:.2f}".rstrip("0").rstrip(".")


def _shape_points(shape: str, cx: float, cy: float, r: float) -> list[tuple[float, float]]:
    """多角形の頂点を返す（hexagon / triangle 用）。"""
    if shape == "hexagon":
        return [
            (cx + r * math.cos(math.radians(-90 + i * 60)),
             cy + r * math.sin(math.radians(-90 + i * 60)))
            for i in range(6)
        ]
    if shape == "triangle":
        return [(cx, cy - r), (cx - r * 0.9, cy + r * 0.8), (cx + r * 0.9, cy + r * 0.8)]
    raise LogoError(f"多角形ではない shape です: {shape!r}")


def _shield_path(cx: float, cy: float, r: float) -> str:
    return (
        f"M {_num(cx)} {_num(cy - r)} "
        f"L {_num(cx + r)} {_num(cy - r * 0.6)} "
        f"L {_num(cx + r)} {_num(cy + r * 0.1)} "
        f"Q {_num(cx + r)} {_num(cy + r * 0.75)} {_num(cx)} {_num(cy + r)} "
        f"Q {_num(cx - r)} {_num(cy + r * 0.75)} {_num(cx - r)} {_num(cy + r * 0.1)} "
        f"L {_num(cx - r)} {_num(cy - r * 0.6)} Z"
    )


def _shape_elements(shape: str, cx: float, cy: float, r: float,
                    style: str, primary: str, accent: str) -> list[str]:
    """スタイルに応じた塗り・線で図形要素を返す。"""
    if style == "monogram":
        fill, stroke, sw = primary, "none", 0
    elif style == "badge":
        fill, stroke, sw = primary, accent, r * 0.08
    elif style == "minimal":
        fill, stroke, sw = "none", primary, r * 0.08
    elif style == "geometric":
        fill, stroke, sw = accent, "none", 0
    else:  # validate_spec 経由では到達しない
        raise LogoError(f"style が不明です: {style!r}")

    def attrs() -> str:
        if stroke == "none":
            return f'fill="{fill}"'
        return f'fill="{fill}" stroke="{stroke}" stroke-width="{_num(sw)}"'

    if shape == "circle":
        return [f'<circle cx="{_num(cx)}" cy="{_num(cy)}" r="{_num(r)}" {attrs()}/>'
                ]
    if shape == "rounded-square":
        return [f'<rect x="{_num(cx - r)}" y="{_num(cy - r)}" '
                f'width="{_num(2 * r)}" height="{_num(2 * r)}" '
                f'rx="{_num(r * 0.25)}" {attrs()}/>']
    if shape in ("hexagon", "triangle"):
        pts = " ".join(f"{_num(x)},{_num(y)}" for x, y in _shape_points(shape, cx, cy, r))
        return [f'<polygon points="{pts}" {attrs()}/>']
    if shape == "shield":
        return [f'<path d="{_shield_path(cx, cy, r)}" {attrs()}/>']
    if shape == "badge":
        # 二重円：外円が本体、内円がアクセントの輪
        inner_sw = r * 0.05
        inner = (f'<circle cx="{_num(cx)}" cy="{_num(cy)}" r="{_num(r * 0.78)}" '
                 f'fill="none" stroke="{accent}" stroke-width="{_num(inner_sw)}"/>')
        return [f'<circle cx="{_num(cx)}" cy="{_num(cy)}" r="{_num(r)}" {attrs()}/>',
                inner]
    raise LogoError(f"shape が不明です: {shape!r}")


def build_svg(spec) -> str:
    """正規化済み（または未検証の）仕様から SVG 文字列を生成する。

    テキストは XML エスケープする。script 要素やイベントハンドラは
    一切出力しない。
    """
    s = validate_spec(spec)
    size = s["size"]
    brand = escape(s["brand"])
    tagline = escape(s["tagline"])
    init = escape(initials(s["brand"]))

    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="0 0 {size} {size}" role="img">'
    ]
    if s["background"] != "transparent":
        parts.append(f'<rect width="{size}" height="{size}" fill="{s["background"]}"/>')

    layout = s["layout"]
    if layout == "icon-top":
        cx, cy, r = size / 2, size * 0.28, size * 0.22
        parts.extend(_shape_elements(s["shape"], cx, cy, r, s["style"], s["primary"], s["accent"]))
        parts.append(_initials_text(cx, cy, r, init, s))
        parts.append(
            f'<text x="{_num(size / 2)}" y="{_num(size * 0.64)}" text-anchor="middle" '
            f'font-family="system-ui, sans-serif" font-size="{_num(size * 0.10)}" '
            f'font-weight="700" fill="{s["text_color"]}">{brand}</text>')
        if tagline:
            parts.append(
                f'<text x="{_num(size / 2)}" y="{_num(size * 0.75)}" text-anchor="middle" '
                f'font-family="system-ui, sans-serif" font-size="{_num(size * 0.05)}" '
                f'fill="{s["text_color"]}" opacity="0.7">{tagline}</text>')
    elif layout == "icon-left":
        cx, cy, r = size * 0.22, size / 2, size * 0.18
        parts.extend(_shape_elements(s["shape"], cx, cy, r, s["style"], s["primary"], s["accent"]))
        parts.append(_initials_text(cx, cy, r, init, s))
        tx = size * 0.45
        parts.append(
            f'<text x="{_num(tx)}" y="{_num(size * 0.48)}" '
            f'font-family="system-ui, sans-serif" font-size="{_num(size * 0.11)}" '
            f'font-weight="700" fill="{s["text_color"]}">{brand}</text>')
        if tagline:
            parts.append(
                f'<text x="{_num(tx)}" y="{_num(size * 0.61)}" '
                f'font-family="system-ui, sans-serif" font-size="{_num(size * 0.05)}" '
                f'fill="{s["text_color"]}" opacity="0.7">{tagline}</text>')
    elif layout == "icon-only":
        cx, cy, r = size / 2, size / 2, size * 0.32
        parts.extend(_shape_elements(s["shape"], cx, cy, r, s["style"], s["primary"], s["accent"]))
        parts.append(_initials_text(cx, cy, r, init, s))
    elif layout == "text-only":
        parts.append(
            f'<text x="{_num(size / 2)}" y="{_num(size * 0.48)}" text-anchor="middle" '
            f'font-family="system-ui, sans-serif" font-size="{_num(size * 0.13)}" '
            f'font-weight="700" fill="{s["text_color"]}">{brand}</text>')
        if tagline:
            parts.append(
                f'<text x="{_num(size / 2)}" y="{_num(size * 0.61)}" text-anchor="middle" '
                f'font-family="system-ui, sans-serif" font-size="{_num(size * 0.05)}" '
                f'fill="{s["text_color"]}" opacity="0.7">{tagline}</text>')
    else:  # validate_spec 経由では到達しない
        raise LogoError(f"layout が不明です: {layout!r}")

    # geometric スタイルの小さなアクセントマーク（図形の右上に重ねる）
    if layout != "text-only" and s["style"] == "geometric":
        if layout == "icon-top":
            cx, cy, r = size / 2, size * 0.28, size * 0.22
        elif layout == "icon-left":
            cx, cy, r = size * 0.22, size / 2, size * 0.18
        else:
            cx, cy, r = size / 2, size / 2, size * 0.32
        parts.append(
            f'<circle cx="{_num(cx + r * 0.55)}" cy="{_num(cy - r * 0.55)}" '
            f'r="{_num(r * 0.16)}" fill="{s["primary"]}"/>')

    parts.append("</svg>")
    return "".join(parts)


def _initials_text(cx: float, cy: float, r: float, init: str, spec: dict) -> str:
    """図形の中心にイニシャルを描く。"""
    if spec["style"] == "minimal":
        fill = spec["primary"]
    else:
        fill = "#ffffff"
    font_size = r * 0.9 if len(init) == 1 else r * 0.7
    return (
        f'<text x="{_num(cx)}" y="{_num(cy)}" text-anchor="middle" '
        f'dominant-baseline="central" font-family="system-ui, sans-serif" '
        f'font-size="{_num(font_size)}" font-weight="700" fill="{fill}">{init}</text>'
    )
