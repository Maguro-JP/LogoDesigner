"""LogoDesigner を AtelIer の拡張として付ける（atelier/extensions.py の口）。

本体はこのパッケージを読まない。拡張の置き場（ProgramData\\AtelIer\\extensions\\LogoDesigner\\）に
extension.json と一緒に置かれ、本体の窓に「ロゴデザイン」のメニューと、ロゴを作るダイアログを足す。
ロゴの生成は LogoDesigner 本体の logo_core（検証と SVG 生成、標準ライブラリのみ）を使う。
このファイルは AtelIer の中で動くので、画面には AtelIer と同じ PySide6 を使う。
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QAction, QImage, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import (QComboBox, QDialog, QFileDialog, QFormLayout, QHBoxLayout,
                               QLabel, QLineEdit, QMenu, QMessageBox, QPushButton, QSpinBox,
                               QVBoxLayout)

MENU = "ロゴデザイン"

SHAPE_LABELS = (("circle", "円"), ("rounded-square", "角丸四角"), ("hexagon", "六角形"),
                ("shield", "盾"), ("triangle", "三角形"), ("badge", "バッジ"))
STYLE_LABELS = (("monogram", "モノグラム"), ("badge", "バッジ"), ("minimal", "ミニマル"), ("geometric", "幾何学"))
LAYOUT_LABELS = (("icon-top", "アイコン上"), ("icon-left", "アイコン左"), ("icon-only", "アイコンのみ"), ("text-only", "文字のみ"))


def load_core():
    """logo_core を探して読む。置き場に一緒に入れた物（インストール時）を先に、
    無ければこのリポジトリの根の物（開発時）を使う"""
    here = Path(__file__).resolve()
    candidates = [here.parents[1] / "logo_core.py",          # 拡張の置き場 / atelier_extension の直下
                  here.parents[2] / "logo_core.py"]          # リポジトリの根
    for path in candidates:
        if path.is_file():
            spec = importlib.util.spec_from_file_location("logo_designer_core", path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            return mod
    raise ImportError("logo_core.py が見つかりません")


class LogoDialog(QDialog):
    """ロゴの仕様を選び、プレビューを見て、SVG / PNG で保存するダイアログ"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.core = load_core()
        self.setWindowTitle("ロゴを作る")
        self.brand = QLineEdit("AtelIer")
        self.tagline = QLineEdit("")
        self.shape = self._combo(SHAPE_LABELS)
        self.style = self._combo(STYLE_LABELS)
        self.layout = self._combo(LAYOUT_LABELS)
        self.primary = QLineEdit("#2563eb")
        self.accent = QLineEdit("#f59e0b")
        self.text_color = QLineEdit("#111827")
        self.background = QLineEdit("#ffffff")
        self.size = QSpinBox()
        self.size.setRange(128, 2048)
        self.size.setValue(512)
        form = QFormLayout()
        form.addRow("ブランド名", self.brand)
        form.addRow("タグライン", self.tagline)
        form.addRow("形", self.shape)
        form.addRow("スタイル", self.style)
        form.addRow("レイアウト", self.layout)
        form.addRow("メイン色 (#RRGGBB)", self.primary)
        form.addRow("アクセント色", self.accent)
        form.addRow("文字色", self.text_color)
        form.addRow("背景色（transparent で透明）", self.background)
        form.addRow("大きさ", self.size)
        self.preview = QLabel()
        self.preview.setAlignment(Qt.AlignCenter)
        self.preview.setMinimumSize(320, 320)
        self.status = QLabel("")
        save_svg = QPushButton("SVGで保存…")
        save_png = QPushButton("PNGで保存…")
        close = QPushButton("閉じる")
        save_svg.clicked.connect(self._save_svg)
        save_png.clicked.connect(self._save_png)
        close.clicked.connect(self.accept)
        row = QHBoxLayout()
        row.addWidget(save_svg)
        row.addWidget(save_png)
        row.addStretch(1)
        row.addWidget(close)
        lay = QVBoxLayout(self)
        lay.addLayout(form)
        lay.addWidget(self.preview)
        lay.addWidget(self.status)
        lay.addLayout(row)
        for w in (self.brand, self.tagline, self.primary, self.accent, self.text_color, self.background):
            w.textChanged.connect(self._refresh)
        for w in (self.shape, self.style, self.layout):
            w.currentIndexChanged.connect(self._refresh)
        self.size.valueChanged.connect(self._refresh)
        self._refresh()

    @staticmethod
    def _combo(labels):
        box = QComboBox()
        for key, label in labels:
            box.addItem(label, key)
        return box

    def spec(self) -> dict:
        """今の入力を仕様 dict にする（検証は core が行う）"""
        return {"brand": self.brand.text(), "tagline": self.tagline.text(),
                "shape": self.shape.currentData(), "style": self.style.currentData(),
                "layout": self.layout.currentData(), "primary": self.primary.text(),
                "accent": self.accent.text(), "text_color": self.text_color.text(),
                "background": self.background.text(), "size": self.size.value()}

    def current_svg(self) -> str:
        """今の入力でロゴの SVG を作る。入力が不正なら core のエラーをそのまま上げる"""
        return self.core.build_svg(self.core.validate_spec(self.spec()))

    def _refresh(self):
        try:
            svg = self.current_svg()
        except Exception as e:   # noqa: BLE001  入力の誤りはプレビューの代わりに理由を出す
            self.status.setText(str(e))
            self.preview.setPixmap(QPixmap())
            return
        self.status.setText("")
        renderer = QSvgRenderer(svg.encode("utf-8"))
        pix = QPixmap(320, 320)
        pix.fill(Qt.transparent)
        p = QPainter(pix)
        renderer.render(p)
        p.end()
        self.preview.setPixmap(pix)

    def _save_svg(self):
        try:
            svg = self.current_svg()
        except Exception as e:   # noqa: BLE001
            QMessageBox.warning(self, "ロゴを作れません", str(e))
            return
        path, _ = QFileDialog.getSaveFileName(self, "SVGで保存", "logo.svg", "SVG (*.svg)")
        if path:
            Path(path).write_text(svg, encoding="utf-8")

    def _save_png(self):
        try:
            svg = self.current_svg()
            size = self.core.validate_spec(self.spec())["size"]
        except Exception as e:   # noqa: BLE001
            QMessageBox.warning(self, "ロゴを作れません", str(e))
            return
        path, _ = QFileDialog.getSaveFileName(self, "PNGで保存", "logo.png", "PNG (*.png)")
        if path:
            renderer = QSvgRenderer(svg.encode("utf-8"))
            img = QImage(size, size, QImage.Format_ARGB32)
            img.fill(Qt.transparent)
            p = QPainter(img)
            renderer.render(p)
            p.end()
            img.save(path, "PNG")


class LogoExtension:
    name = "logo-designer"

    def attach(self, window) -> None:
        menu = QMenu(MENU, window)
        act = QAction("ロゴを作る…", window)
        act.setToolTip("ブランド名と形・色からロゴを作り、SVG / PNG で保存します")
        act.triggered.connect(lambda _=False: LogoDialog(window).exec())
        menu.addAction(act)
        window.menuBar().addMenu(menu)
        window.logo_designer_menu = menu   # 窓に参照を持たせる（メニューが消えないように）


EXTENSION = LogoExtension()
