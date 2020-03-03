# TODO
1. [ ] 徐々にPillow/OpenCV+Numpyに置き換える事!!
   - ~~Pillowは2MB, OpenCVは約50MB. Pillowも少しなれるか。cropにもPillow使えるので問題ない？~~
   - Pillow: OpenCVと重複する。OpenCVになれる事にする。
- [ ] .aiを.eps/.pngへ変換可能へ
- [ ] mermaidを画像化
- [x] 出力時の日時datetimeを併記
- [ ] raise Exceptionを全て排除。エラーでいちいち留めない。例外処理を追加して
- [ ] bin(soffice, imagemagick'convert and so on)の存在確認
- [ ] pdfは透過png?が黒くなるためデフォルトはpng
- [ ] dstとsrcフォルダの生成、実行時に。
- [ ] LibreOffice Vanilla.appは変換失敗するので、注意を促す

# Tips

- Path.resolve()をつかえ、相対pathの引数をi