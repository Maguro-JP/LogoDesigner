# CHANGELOG

## v1.0.0 — 2026-11-24

- LogoDesigner の最初のリリース。
- `logo_core.py` を追加：仕様 `logodesigner.logo.v1` の検証・正規化、イニシャル生成、SVG 生成（6 種類の形、4 種類のスタイル、4 種類のレイアウト）。
- `server.py` を追加：localhost（127.0.0.1:8767）専用サーバー。`POST /api/logo?format=svg` で SVG を返す。
- `index.html` を追加：日本語のシングルページ UI。ライブプレビュー、プリセット、SVG / PNG / JSON 保存、SVG コピー、localStorage への設定保存。
- `test_logo_core.py` を追加：検証・イニシャル・SVG 生成のテスト。
- `docs/logo-core.md`、`docs/integration.md`、`AGENTS.md`、`.gitignore` を追加。
