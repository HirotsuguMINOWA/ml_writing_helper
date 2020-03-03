# ML Writing Helper

## CLI
- 書式: `convert4ml src_path dst_dir to_fmt is_crop`

### watcher
- 書式: `mlhelper.watch`

## Usage

## Caution

## 複数の連番ファイル(file-0.eps,file-1.eps,...)で出力される
- 解決方法: 1頁目以外非表示にする(@powerpointで確認)
  - スライド(PowerPoint/odp too?)もLibreOffice 6.3.4?から1頁目以外も変換後pdfに含まれるようになってしまったので、
  - .epsによく起こりがち？

## 注意@Design

- LaTeXには`.eps`
  - 現在, pdfはcropができてない。cropできるならpdfの方がよいかも。
  - eps変換は画質劣化が生じる。pdfからの変換
- Markdownには`.png`へ変換がよい


# 未整理

- epsへの変換はpdfからする事
  - pngからepsへ変換するとboudingbox取得失敗する？みたい

## LaTeXにはpdfよりeps
- 理由: 適切なサイズで表示される
  - pdfでは、`\linewidth`で正しく幅(複数列)に収まらない,pdfのサイズが正しく取得できていないためと思われる。
    - pngに比べbouindingboxの指定が不要bouindingboxは単なるサイズ指定ではないので、epsか.xbbを使う方が楽。
  - IEICEのテンプレでは、上記サイズ取得の失敗のためか、普通に画像出力で、文字の中に埋もれた
