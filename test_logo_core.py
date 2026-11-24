"""logo_core.py のテスト。"""

import unittest

from logo_core import LogoError, build_svg, initials, validate_spec


def base(**overrides):
    spec = {"brand": "Maguro", "tagline": "つくる、たのしむ。"}
    spec.update(overrides)
    return spec


class TestValidateSpec(unittest.TestCase):
    def test_valid_spec_normalisation_and_defaults(self):
        spec = validate_spec({"brand": "  Maguro  "})
        self.assertEqual(spec["format"], "logodesigner.logo.v1")
        self.assertEqual(spec["brand"], "Maguro")
        self.assertEqual(spec["tagline"], "")
        self.assertEqual(spec["shape"], "circle")
        self.assertEqual(spec["style"], "monogram")
        self.assertEqual(spec["layout"], "icon-top")
        self.assertEqual(spec["size"], 512)
        self.assertEqual(spec["primary"], "#2563EB".lower())
        self.assertEqual(spec["background"], "#ffffff")

    def test_hex_is_lowercased(self):
        spec = validate_spec(base(primary="#ABCDEF"))
        self.assertEqual(spec["primary"], "#abcdef")

    def test_transparent_background(self):
        spec = validate_spec(base(background="transparent"))
        self.assertEqual(spec["background"], "transparent")
        spec = validate_spec(base(background="Transparent"))
        self.assertEqual(spec["background"], "transparent")

    def test_hex_validation(self):
        for bad in ["red", "#12345", "#1234567", "#GGGGGG", "2563eb", 123, None]:
            with self.subTest(bad=bad), self.assertRaises(LogoError):
                validate_spec(base(primary=bad))
        for bad in ["#12345", "transparent ", ""]:
            with self.subTest(bad=bad), self.assertRaises(LogoError):
                validate_spec(base(background=bad))

    def test_unknown_shape_style_layout(self):
        with self.assertRaises(LogoError):
            validate_spec(base(shape="star"))
        with self.assertRaises(LogoError):
            validate_spec(base(style="fancy"))
        with self.assertRaises(LogoError):
            validate_spec(base(layout="diagonal"))

    def test_empty_and_too_long_brand(self):
        for bad in ["", "   ", None, 123]:
            with self.subTest(bad=bad), self.assertRaises(LogoError):
                validate_spec(base(brand=bad))
        with self.assertRaises(LogoError):
            validate_spec(base(brand="x" * 31))
        # 30 文字は通る
        self.assertEqual(validate_spec(base(brand="x" * 30))["brand"], "x" * 30)
        with self.assertRaises(LogoError):
            validate_spec({})

    def test_tagline_limit(self):
        with self.assertRaises(LogoError):
            validate_spec(base(tagline="x" * 61))
        self.assertEqual(validate_spec(base(tagline="x" * 60))["tagline"], "x" * 60)

    def test_size_bounds(self):
        for bad in [127, 2049, 0, -1, 512.0, 512.5, "512", True, float("nan"), float("inf")]:
            with self.subTest(bad=bad), self.assertRaises(LogoError):
                validate_spec(base(size=bad))
        self.assertEqual(validate_spec(base(size=128))["size"], 128)
        self.assertEqual(validate_spec(base(size=2048))["size"], 2048)

    def test_control_characters_rejected(self):
        with self.assertRaises(LogoError):
            validate_spec(base(brand="Maguro\x01"))
        with self.assertRaises(LogoError):
            validate_spec(base(tagline="hello\nworld"))

    def test_bad_format_and_non_dict(self):
        with self.assertRaises(LogoError):
            validate_spec(base(format="other.v1"))
        with self.assertRaises(LogoError):
            validate_spec("not a dict")
        with self.assertRaises(LogoError):
            validate_spec(None)


class TestInitials(unittest.TestCase):
    def test_multi_word(self):
        self.assertEqual(initials("Maguro Design"), "MD")
        self.assertEqual(initials("maguro jp"), "MJ")

    def test_single_word(self):
        self.assertEqual(initials("Maguro"), "MA")
        self.assertEqual(initials("A"), "A")

    def test_japanese_falls_back_to_first_character(self):
        self.assertEqual(initials("まぐろ"), "ま")
        self.assertEqual(initials("鮪デザイン"), "鮪")

    def test_empty_raises(self):
        with self.assertRaises(LogoError):
            initials("")
        with self.assertRaises(LogoError):
            initials("   ")


class TestBuildSvg(unittest.TestCase):
    def test_svg_contains_shape_and_escaped_brand(self):
        svg = build_svg(base(brand="A<B & C"))
        self.assertIn("<svg", svg)
        self.assertIn('xmlns="http://www.w3.org/2000/svg"', svg)
        self.assertIn('width="512"', svg)
        self.assertIn("<circle", svg)
        self.assertIn("A&lt;B &amp; C", svg)
        self.assertNotIn("<script", svg)
        self.assertNotIn("onload", svg)
        self.assertNotIn("A<B", svg)

    def test_all_shapes_present(self):
        expectations = {
            "circle": "<circle",
            "rounded-square": "<rect",
            "hexagon": "<polygon",
            "triangle": "<polygon",
            "shield": "<path",
            "badge": "<circle",
        }
        for shape, tag in expectations.items():
            with self.subTest(shape=shape):
                self.assertIn(tag, build_svg(base(shape=shape)))

    def test_layout_variants_produce_different_svg(self):
        svgs = {layout: build_svg(base(layout=layout))
                for layout in ("icon-top", "icon-left", "icon-only", "text-only")}
        self.assertEqual(len(set(svgs.values())), 4)
        # text-only には図形もイニシャルもない
        self.assertNotIn("<circle", svgs["text-only"])
        self.assertNotIn("MA", svgs["text-only"])
        # icon-only にはブランド名のテキストがない（イニシャルはある）
        self.assertIn("MA", svgs["icon-only"])

    def test_transparent_background_has_no_background_rect(self):
        svg = build_svg(base(background="transparent"))
        # 背景 rect は width/height=size の rect だけ。図形の rect は別物。
        self.assertNotIn(f'<rect width="512" height="512"', svg)
        svg2 = build_svg(base(background="#ffffff"))
        self.assertIn(f'<rect width="512" height="512" fill="#ffffff"/>', svg2)

    def test_invalid_spec_raises_in_build_svg(self):
        with self.assertRaises(LogoError):
            build_svg(base(brand=""))


if __name__ == "__main__":
    unittest.main()
