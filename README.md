# LogoDesigner

ブランド名と形・色を選ぶだけの、シンプルなロゴ作成ツールです。
ブラウザでロゴをプレビューし、SVG / PNG / JSON として保存できます。

## できること

- ブランド名（必須）とタグライン（任意）からロゴを作る
- 形を 6 種類から選ぶ：円 / 角丸四角 / 六角形 / 盾 / 三角形 / バッジ
- スタイルを 4 種類から選ぶ：モノグラム / バッジ / ミニマル / 幾何学
- レイアウトを 4 種類から選ぶ：アイコン上 / アイコン左 / アイコンのみ / 文字のみ
- メイン色・アクセント色・背景色・文字色を自由に選ぶ（背景は透明にもできる）
- プリセット（モノグラム / バッジ / ミニマル / 幾何学）をワンクリックで適用する
- プレビューを見ながら SVG・PNG・JSON を保存する。設定はブラウザの localStorage に保存される

## 起動方法

Python 3.10 以上が必要です。追加のパッケージは不要です（標準ライブラリのみ）。

```bash
cd LogoDesigner
python3 server.py
```

ブラウザで http://127.0.0.1:8767/ を開きます。

サーバーを使わず `index.html` を直接開いても、プレビューとブラウザ内での保存は使えます。
その場合は SVG 保存がサーバー経由ではなくブラウザ内で作った SVG になります。

## API

### POST /api/logo?format=svg

仕様 JSON を送ると、正規化された SVG を `logo.svg` として返します。

```bash
curl -X POST "http://127.0.0.1:8767/api/logo?format=svg" \
  -H "Content-Type: application/json" \
  -d '{"brand": "Maguro", "tagline": "つくる、たのしむ。", "shape": "circle", "style": "monogram", "layout": "icon-top", "size": 512}' \
  -o logo.svg
```

入力が不正な場合は 400 と `{"error": "..."}` を返します。
リクエスト本文の上限は 256KB です。

仕様の詳細は [docs/logo-core.md](docs/logo-core.md) を参照してください。

## 現在の限界

- AI による画像生成はできません。形・色・文字の組み合わせでロゴを作ります。
- フォントは埋め込みません。SVG は system-ui など環境のフォントで表示されます。
- サーバー側の PNG 出力はありません。PNG はブラウザで SVG を描画して作ります。
- 使える文字はブランド名（30文字以内）とタグライン（60文字以内）のみです。
- 対応する形・スタイル・レイアウトは画面と `docs/logo-core.md` にあるものだけです。
- サーバーは localhost（127.0.0.1:8767）専用で、外部からはアクセスできません。

## 検証

```bash
python3 -m unittest -v test_logo_core.py
```

## ファイル構成

- `logo_core.py` — 仕様の検証・正規化・SVG 生成（純粋なロジック）
- `server.py` — localhost 専用サーバー（`POST /api/logo?format=svg`）
- `index.html` — 日本語のシングルページ UI（外部依存なし）
- `test_logo_core.py` — `logo_core.py` のテスト
- `docs/logo-core.md` — 仕様 `logodesigner.logo.v1` の詳細
- `docs/integration.md` — 他の Designer リポジトリとの連携
