# TODO
1. [ ] .bibファイル内にコピー時にurl欄を"\url{}"でラップする事。するとURL内で改行できる。
   2. Ref: https://texfaq.org/FAQ-citeURL
   ```latex
   @misc{...,
   ...,
   howpublished = "\url{http://...}"
   }
   ```
1. [ ] Folder(fig_src/figなど)なければ生成確認(yes/no)。→強制作成モード(CLIパラに指定する方法が)が必要。VSCodeではY/N選べない。
2. [ ] .bibの同期において、.bibファイルがなければ、最初はCOPYする事
1. [ ] 白黒出力モードのサポート
   - 科研なんかで白黒で判断したい画像もあるため。船の小火をAIが火災と判断している率を%で表示するため。
2. [ ] 徐々にPillow/OpenCV+Numpyに置き換える事!!
   - ~~Pillowは2MB, OpenCVは約50MB. Pillowも少しなれるか。cropにもPillow使えるので問題ない？~~
   - Pillow: OpenCVと重複する。OpenCVになれる事にする。
3. [ ] PDFCropMarginをつかってみる
   1. PythonからPDFの余白を除去できる
      1. https://pypi.org/project/pdfCropMargins/
- ~~PythonMagicなるライブラリがあるらしい。使う？~~
  - `python-magic`
- [ ] ~~.aiを.eps/.pngへ変換可能へ~~
- [ ] mermaidを画像化
- [X] 出力時の日時datetimeを併記
- [ ] raise Exceptionを全て排除。エラーでいちいち留めない。例外処理を追加して
- [ ] bin(soffice, imagemagick'convert and so on)の存在確認
- [ ] pdfは透過png?が黒くなるためデフォルトはpng
- [ ] dstとsrcフォルダの生成、実行時に。
- [ ] LibreOffice Vanilla.appは変換失敗するので、注意を促す
- [ ] PlantUML変換失敗の要修正

# Tips

- Path.resolve()をつかえ、相対pathの引数を

# Useful Library

- Pandoc (mentioned before) -- can convert from MD to PPT. This might be the best bet for a solution, since it's complete and mature.
- odpdown -- Python library that converts to the OpenOffice Presenter format, which can be used for PPTs. Adding Python to the toolchain doesn't sound desirable, though.
- officegen -- do a lot of code-rolling for this project, but it matches the Electron toolchain. CBA: Yuck!
