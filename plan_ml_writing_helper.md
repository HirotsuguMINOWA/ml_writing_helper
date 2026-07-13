# milestone

## JSONフォーマット
- mode:copy
  - src_path: str型:コピー元のPATH(DIR)
  - dst_path: str型: 複数指定可
  - patterns: strリスト型: コピーする正規表現
- mode:img_conv
  - src_path: str型: 変換元のPATH
  - dst_path: str型: 変換した画像を保存先
  - dst_format: 変換後のformat(単一)
- mode: document変換
  - src_path:str型: 変換元のPATH
  - src_format:リストstr型: .md, .htmlなど複数指定可能
  - dst_format:リストstr型: pdf, html, docx複数出力

## 1. md2pdfをMLWritingHelperへ統合
- [ ] md2pdf.pyの`MarkdownConverter`クラスをMLWritingHelperにインポート
- [ ] 既存のテキスト変換パイプラインに変換エンジン（pandoc/marp/slidev）を追加
- [ ] MLWritingHelperの出力形式に `pdf`、`html`、`docx` オプションを統合
- [ ] 変換後のファイル出力先を設定可能にする
- [ ] marp-cli、slidev、pandocの依存チェック機能を統合

## 2. CLIパラメータを.jsonファイルで指定
- [ ] JSON設定ファイルスキーマを定義（例: `config.json`）
- [ ] CLIパラメータをJSONから読み込む機能を実装
- [ ] CLI引数とJSON設定のマージロジックを実装（CLI引数が優先）
- [ ] JSONバリデーション機能を追加
- [ ] サンプル設定ファイルを提供

### JSON設定ファイルの構造（案）
```json
{
  "root_src": "/path/to/source",
  "root_dest": "/path/to/output",
  "input_extensions": [".md", ".html"],
  "copy_extensions": [".png", ".jpg", ".svg"],
  "output_formats": ["pdf", "html"],
  "header_files": ["/path/to/header.tex"],
  "marp_header_files": ["/path/to/marp_header.yaml"],
  "engine": "auto",
  "log_level": "DEBUG"
}
```

## 3. Nuitka + GitHub CI/CDでBuild
- [ ] Nuitkaビルド設定ファイル（`build_config.py`）を作成
- [ ] GitHub Actionsワークフロー（`.github/workflows/build.yml`）を作成
- [ ] 複数プラットフォーム対応（macOS、Windows、Linux）
- [ ] ビルド成果物をGitHub Releasesにアップロード
- [ ] PyInstallerとの比較検討（必要に応じて）
- [ ] 依存パッケージのバンドル確認（marp-cli等）

### ビルドプロセス（案）
1. Nuitkaで単一実行ファイルにコンパイル
2. marp-cliバイナリをバンドル
3. pandoc、slideyvが利用可能か確認
4. テスト実行
5. Releasesに自動アップロード
