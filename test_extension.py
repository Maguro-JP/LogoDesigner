"""AtelIer 拡張の試験。拡張の形、ダイアログでロゴが作れること、本体の置き場読み込みで登録できること"""
import json
import os
import shutil
import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "atelier_extension"))

try:
    from PySide6.QtWidgets import QApplication, QMainWindow
    HAS_QT = True
except ImportError:
    HAS_QT = False


def _app():
    return QApplication.instance() or QApplication([])


@unittest.skipUnless(HAS_QT, "PySide6 が無い環境では拡張の試験をしない")
class ExtensionShapeTest(unittest.TestCase):
    def test_manifest_and_object(self):
        spec = json.loads((ROOT / "atelier_extension" / "extension.json").read_text(encoding="utf-8"))
        self.assertEqual(spec["module"], "logo_designer.extension")
        self.assertEqual(spec["attr"], "EXTENSION")
        from logo_designer.extension import EXTENSION
        self.assertEqual(EXTENSION.name, "logo-designer")
        self.assertTrue(callable(EXTENSION.attach))

    def test_attach_adds_menu(self):
        _app()
        from logo_designer.extension import EXTENSION
        win = QMainWindow()
        EXTENSION.attach(win)
        titles = [a.text() for a in win.menuBar().actions()]
        self.assertIn("ロゴデザイン", titles)


@unittest.skipUnless(HAS_QT, "PySide6 が無い環境では拡張の試験をしない")
class DialogTest(unittest.TestCase):
    def setUp(self):
        _app()
        from logo_designer.extension import LogoDialog
        self.dlg = LogoDialog()

    def test_default_svg_builds(self):
        svg = self.dlg.current_svg()
        self.assertIn("<svg", svg)
        self.assertIn("AtelIer", svg)

    def test_empty_brand_is_an_error(self):
        self.dlg.brand.setText("")
        # core は拡張がファイルの場所から読むため、例外のクラスは import した物と別物になる。ValueError として見る
        with self.assertRaises(ValueError):
            self.dlg.current_svg()
        self.assertNotEqual(self.dlg.status.text(), "")


class DropInLoadTest(unittest.TestCase):
    """本体（AtelIer）の load_dropins で、インストールした形のフォルダが登録できること"""

    def test_loads_through_atelier(self):
        atelier_home = os.environ.get("ATELIER_HOME", str(ROOT.parent / "AtelIer-work"))
        if not (Path(atelier_home) / "atelier" / "extensions.py").is_file():
            self.skipTest("AtelIer のソースが近くに無い")
        sys.path.insert(0, atelier_home)
        from atelier import extensions
        with TemporaryDirectory() as d:
            dst = Path(d) / "LogoDesigner"
            shutil.copytree(ROOT / "atelier_extension", dst)
            shutil.copy2(ROOT / "logo_core.py", dst / "logo_core.py")
            names = extensions.load_dropins(Path(d))
            self.assertIn("logo-designer", names)
            self.assertIn("logo-designer", [e.name for e in extensions.registered()])


if __name__ == "__main__":
    unittest.main()
