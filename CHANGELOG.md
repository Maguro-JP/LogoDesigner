# CHANGELOG

## v1.1.0 — 2026-11-27

- AtelIer の拡張を追加（`atelier_extension/`）。AtelIer の拡張の置き場に入れると、「ロゴデザイン」のメニューからロゴを作るダイアログが開き、プレビューを見ながら SVG / PNG で保存できる。生成は `logo_core.py` をそのまま使う。
- `atelier_extension/install.ps1` を追加：拡張一式と `logo_core.py` を `C:\ProgramData\AtelIer\extensions\LogoDesigner\` へ入れる。
- `test_extension.py` を追加：拡張の形、ダイアログの生成、本体の置き場読み込み（load_dropins）での登録のテスト。

## v1.0.0 — 2026-11-24

- LogoDesigner の最初のリリース。
- `logo_core.py` を追加：仕様 `logodesigner.logo.v1` の検証・正規化、イニシャル生成、SVG 生成（6 種類の形、4 種類のスタイル、4 種類のレイアウト）。
- `server.py` を追加：localhost（127.0.0.1:8767）専用サーバー。`POST /api/logo?format=svg` で SVG を返す。
- `index.html` を追加：日本語のシングルページ UI。ライブプレビュー、プリセット、SVG / PNG / JSON 保存、SVG コピー、localStorage への設定保存。
- `test_logo_core.py` を追加：検証・イニシャル・SVG 生成のテスト。
- `docs/logo-core.md`、`docs/integration.md`、`AGENTS.md`、`.gitignore` を追加。
