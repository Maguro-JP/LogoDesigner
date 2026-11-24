# 他の Designer リポジトリとの連携

## 概要

LogoDesigner の仕様 JSON は `logodesigner.logo.v1` 形式で、他の Designer 系ツールと
同じ考え方で作られている。中心になるのは「JSON が仕様で、SVG / ファイルが成果物」
という分離で、3DDesigner や FashionDesigner と同じパターンである。

## 形式

```json
{
  "format": "logodesigner.logo.v1",
  "brand": "Maguro",
  "tagline": "つくる、たのしむ。",
  "shape": "circle",
  "style": "monogram",
  "primary": "#2563eb",
  "accent": "#f59e0b",
  "text_color": "#111827",
  "background": "#ffffff",
  "layout": "icon-top",
  "size": 512
}
```

`format` フィールドが形式の識別子になる。読み手はまず `format` を確認し、
`logodesigner.logo.v1` でなければ扱わないこと。

## 他のツールから読む場合

- `brand` / `shape` / `primary` など、必要なフィールドだけ読めばよい。
  未知のフィールドは無視してよい（`validate_spec` も未知のキーを無視する）。
- `brand` は表示名、`shape` は図形の種類、`primary` / `accent` は色として
  そのまま使える。FashionDesigner 風のツールがブランド色として
  `primary` を参照する、といった使い方ができる。
- `size` は SVG の幅・高さ（px）である。

## 他のツールへ渡す場合

- LogoDesigner の JSON 保存（`logo.json`）をそのまま渡す。
- または `POST /api/logo?format=svg` に JSON を送り、返ってきた SVG を使う。
- 受け取った側は、使う前に `logo_core.validate_spec` 相当の検証を通すこと。
  検証を通らない仕様は、そのまま描画してはいけない。

## 3DDesigner / FashionDesigner との関係

- 3DDesigner は `mesh_core.py` で検証とエクスポートを分離している。
  LogoDesigner は同じ分離を `logo_core.py`（検証・SVG 生成）と
  `server.py`（配信・API）で行っている。
- FashionDesigner は設定を localStorage に保存し、canvas から PNG を出す。
  LogoDesigner の `index.html` も同じ方式で、設定を localStorage に保存し、
  PNG はブラウザの canvas で SVG から作る。
- どのツールも、サーバー側で PNG を作ることはしない。
