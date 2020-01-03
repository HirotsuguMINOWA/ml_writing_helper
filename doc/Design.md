# 未整理

- epsへの変換はpdfからする事
  - pngからepsへ変換するとboudingbox取得失敗する？みたい
  ## LaTeXにはpdfよりeps
- 理由: 適切なサイズで表示される
  - pdfでは、`\linewidth`で正しく幅(複数列)に収まらない,pdfのサイズが正しく取得できていないためと思われる。
    - pngに比べbouindingboxの指定が不要bouindingboxは単なるサイズ指定ではないので、epsか.xbbを使う方が楽。
  - IEICEのテンプレでは、上記サイズ取得の失敗のためか、普通に画像出力で、文字の中に埋もれた
