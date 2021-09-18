# ML Writing Helper

## CLI(未実装)
- 書式: `convert4ml src_path dst_dir to_fmt is_crop`

### watcher
- 書式: `mlhelper.watch`

## Usage

```python
from ml_writing_helper.main import Monitor
from pathlib import Path
manu_path = Path(__file__).resolve().parent # manuscript_path as hiro_watcher
o=Monitor()

o.set_monitor(
 src_dir=manu_path.joinpath("fig_src")
 ,dst_dir=manu_path.joinpath("fig_gen")
 ,to_fmt=".eps"
)

o.set_monitor(
  src_dir="/usr/<username>/Documents/BibTexExported"
  ,dst_dir=manu_path
  ,to_fmt=".bib"
)

o.start_monitors()
```

## Caution

## 複数の連番ファイル(file-0.eps,file-1.eps,...)で出力される
- 解決方法: 1頁目以外非表示にする(@powerpointで確認)
  - スライド(PowerPoint/odp too?)もLibreOffice 6.3.4?から1頁目以外も変換後pdfに含まれるようになってしまったので、
  - .epsによく起こりがち？

## 注意@Design

- LaTeXには`.eps`
  - 現在, pdfはcropができてない。cropできるならpdfの方がよいかも。
  - eps変換は画質劣化が生じる。pdfからの変換
  - epsズレ
    - eps2pdf, pdf2psコマンドでrepairするmethod設けている。
    - convert, matplotlib, matlab?の生成.epsはよくずれる...
- Markdownには`.png`へ変換がよい


# 未整理

- epsへの変換はpdfからする事
  - pngからepsへ変換するとboudingbox取得失敗する？みたい

## LaTeXにはpdfよりeps
- 理由: 適切なサイズで表示される
  - pdfでは、`\linewidth`で正しく幅(複数列)に収まらない,pdfのサイズが正しく取得できていないためと思われる。
    - pngに比べbouindingboxの指定が不要bouindingboxは単なるサイズ指定ではないので、epsか.xbbを使う方が楽。
  - IEICEのテンプレでは、上記サイズ取得の失敗のためか、普通に画像出力で、文字の中に埋もれた

# Troubleshooting

## **Cropされない**
- 見えない枠が対象画像にあるかと。

## スライドが正しく変換できてない
- 手動で対応するしかない。
1. スライドを**.png**へ。
   - pdfへはしない方がよい。crop失敗するから？
2. `.png`化したファイルをmonitoringしているフォルダからMove&Restore。

## PowerPointファイルから画像化(PDF含む)の画質が低い
1. MacOS: LibreOfficeVanillaを使っている
   1. このソフトは変換機能が除去されているらしい
2. その.pttxをLibreOfficeで開いても画質落ちていませんか？
   1. PowerPoint上では画質下がってなくても、LibreOfficeで開くと画質が下がっている場合があり、資料の作り直しで解決できるだろう。
3. MacOS: LibreOfficeのアプリ検証が終わってない？
   1. Homebrewからインスト後、アプリ検証終わってないまま利用すると画質が低い。