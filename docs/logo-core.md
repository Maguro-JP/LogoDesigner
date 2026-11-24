# logo-core 仕様

## フォーマット

`logodesigner.logo.v1`

JSON オブジェクトで表す。`format` を省略した場合は `logodesigner.logo.v1` として扱う。
`format` が他の値の場合はエラーになる。

## フィールド

| フィールド | 型 | 必須 | 既定値 | 備考 |
| --- | --- | --- | --- | --- |
| `format` | 文字列 | 任意 | `logodesigner.logo.v1` | 他の値は拒否 |
| `brand` | 文字列 | 必須 | — | 1〜30 文字。空白だけは不可 |
| `tagline` | 文字列 | 任意 | `""` | 0〜60 文字 |
| `shape` | 文字列 | 任意 | `circle` | 下記参照 |
| `style` | 文字列 | 任意 | `monogram` | 下記参照 |
| `primary` | 文字列 | 任意 | `#2563eb` | `#RRGGBB` |
| `accent` | 文字列 | 任意 | `#f59e0b` | `#RRGGBB` |
| `text_color` | 文字列 | 任意 | `#111827` | `#RRGGBB` |
| `background` | 文字列 | 任意 | `#ffffff` | `#RRGGBB` または `transparent` |
| `layout` | 文字列 | 任意 | `icon-top` | 下記参照 |
| `size` | 整数 | 任意 | `512` | 128〜2048 |

## 検証ルール（`validate_spec`）

- 仕様はオブジェクトでなければならない。そうでなければ `LogoError`。
- `brand` がない、空、31 文字以上、制御文字（`U+0000`〜`U+001F`、`U+007F`）を含む場合はエラー。
- `tagline` が 61 文字以上、または制御文字を含む場合はエラー。
- 色は `#RRGGBB`（16 進 6 桁）のみ。大文字は小文字に正規化する。
- `background` は `#RRGGBB` または `transparent`（大文字・小文字を問わない）のみ。
- `shape` / `style` / `layout` が一覧にない値はエラー。
- `size` は整数のみ。`bool`、浮動小数点数、文字列はエラー。`NaN` / `inf` もエラー。
  範囲は 128〜2048。
- 未知のキーは無視し、正規化した dict には含めない。

## shape

- `circle` — 円
- `rounded-square` — 角丸四角（角半径は辺の 1/4）
- `hexagon` — 六角形。頂点は cos / sin で計算し、上を頂点とする
- `triangle` — 三角形。上を頂点とする
- `shield` — 盾形。パスで描く
- `badge` — 二重円。外円が本体、内円がアクセントの輪

## style

- `monogram` — 図形を `primary` で塗り、白いイニシャルを重ねる
- `badge` — 図形を `primary` で塗り、`accent` の輪郭を付ける
- `minimal` — 図形は塗らず、`primary` の線だけ。イニシャルも `primary`
- `geometric` — 図形を `accent` で塗り、`primary` の小さな円を右上に重ねる。イニシャルは白

## layout

- `icon-top` — 図形を上に、ブランド名とタグラインを下に置く
- `icon-left` — 図形を左に、ブランド名とタグラインを右に置く
- `icon-only` — 図形とイニシャルのみ
- `text-only` — ブランド名とタグラインのみ。図形とイニシャルはない

## initials（`initials(brand)`）

- 複数語の場合：最初の 2 語の頭文字（ASCII 英字）を大文字で返す。例：`Maguro Design` → `MD`
- 1 語の場合：先頭 2 文字（ASCII 英字）を大文字で返す。例：`Maguro` → `MA`
- 日本語など ASCII 英字で始まらない場合：先頭 1 文字をそのまま返す。例：`まぐろ` → `ま`
- 空の場合は `LogoError`

## build_svg（`build_svg(spec)`）

- `validate_spec` で正規化してから生成する。未検証の dict を渡してもよい。
- 幅・高さは `size`、viewBox は `0 0 <size> <size>`、名前空間は `http://www.w3.org/2000/svg`。
- ブランド名・タグライン・イニシャルは `xml.sax.saxutils.escape` でエスケープする。
  `<` は `&lt;`、`&` は `&amp;` になる。
- `background` が `transparent` の場合は背景の rect を出力しない。
- script 要素やイベントハンドラは一切出力しない。
- フォントは埋め込まない。`font-family="system-ui, sans-serif"` を指定する。
