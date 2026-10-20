# ML Writing Helper

[English](ReadMe.md) | [日本語]

## 概要

このパッケージは、LaTeX、HTML、Markdown などのマークアップ言語 (ML) を用いたドキュメントや論文の執筆を支援するツールです。



## 機能

1. 画像挿入のサポート
    1. PowerPoint または LibreOffice で作成した .pptx/.ppt ファイルを、.eps、.pdf、.png などの画像ファイルに変換できます。
1. 切り抜き (トリミング)
    1. 上記の変換時に、外枠の余白 (白い余白) を除去できます。
1. 特定フォルダーの監視と、内部ファイルが変更されたときのコピー
    1. ドキュメントマネージャーからエクスポートされた .bib ファイルなどについて、変更やエクスポートを検出することで、対象フォルダーへコピーできます。
1. グレースケール化
    1. グレースケールの画像に変換できます。
1. ドキュメント変換
    1. Markdown (.md) / HTML ファイルが変更されたときに、PDF、HTML、DOCX へ変換でき、mermaid / PlantUML ダイアグラム、数式 (KaTeX)、Marp / Slidev スライドをレンダリングできます。
1. 小テストのSCORM出力
  1. Markdownで作成した単一選択式の問題をSCORM 1.2形式のZIPパッケージに変換できます。


## パッケージのビルド

- 以下のビルドコマンドは、`pyproject.toml` と Nuitka を用いて実行されます。

```bash
python -m build --wheel
```

## セットアップ

### 必要条件

このパッケージを使用する前に、以下のソフトウェアをインストールしてください。

1. LibreOffice

## CLI


### CLI に関する注意

- CLI の実行は、1 プロセスにつき 1 つのタスクしか実行できません。
- CLI で複数のタスクを実行したい場合は、各タスクごとにこのアプリを実行してください。
  - 複数のタスクを実行したい場合は、`--json` モードを使うことをおすすめします。


### メインコマンド (`ml_writing_helper`)

すべての機能は、単一のコマンド `ml_writing_helper` によって提供されます
(かつての `watch4ml` と `convert4ml` はこれに統合されました。1 回だけ実行するか監視を続けるかは `--monitor` で指定します)。

以下のいずれかのオプションで実行方法を選択します。これらは組み合わせて使用できません。

#### MarkdownからSCORM 1.2を作成

問題ごとに `##` 見出しを付け、選択肢を `- [ ] A. 選択肢` と記述します。正解の選択肢は `[x]` にします。1問につき正解は1つ、選択肢は2つ以上必要です。

```markdown
# Python 基礎

## 変数とは？
値を保存する仕組みです。
- [ ] A. 関数
- [x] B. 名前付きの領域
```

```bash
ml_writing_helper scorm quiz.md --output quiz_scorm12.zip
```

生成したZIPをLMSにコース教材として登録します。受講時に得点と完了状態をSCORM 1.2 APIへ送信します。

| コマンド                                                    | 動作                                                                                       |
| ----------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| `ml_writing_helper` (引数なし) / `ml_writing_helper --help` | ヘルプメッセージを表示                                                                     |
| `ml_writing_helper --json [PATH]`                           | json ファイルからのタスク。PATH なしの場合、`./ml_writing_helper.json` が使用されます      |
| `ml_writing_helper --json '{...}'`                          | JSON 文字列からのタスク (下記参照)                                                         |
| `ml_writing_helper --mode img_conv [params...]`             | モード `img_conv`: CLI パラメータからの 1 つの図表変換タスク                               |
| `ml_writing_helper --mode copy [params...]`                 | モード `copy`: CLI パラメータからのコピータスク                                            |
| `ml_writing_helper --mode doc_conv [params...]`             | モード `doc_conv`: CLI パラメータからの 1 つのドキュメント変換タスク                       |
| `ml_writing_helper --conf-maker-web [PATH]`                 | Web UI (ブラウザ) で json ファイルを作成/編集。PATH なしの場合、`./ml_writing_helper.json` |
| `ml_writing_helper --conf-maker-cli [PATH]`                 | ターミナルで対話的に json ファイルを作成/編集。PATH なしの場合、`./ml_writing_helper.json` |
| `ml_writing_helper scorm INPUT.md --output OUTPUT.zip`      | Markdownの単一選択式問題をSCORM 1.2パッケージに変換                                        |

- `--mode` のパラメータ (`--src`、`--ext`、`--root`、`--log-level` など) は、`--mode` と同時に使用するのみ可能です。`--json` や `--conf-maker-*` の場合は、代わりに json ファイルに記述してください。
- 複数のタスクを一度に実行する (例: img_conv と copy) には、json ファイルを使用してください。

#### 1 回だけ実行するか監視を続けるか (`--monitor`)

- `--monitor` なしの場合、すべてのタスクが 1 回だけ実行され (必要なファイルが変換 / コピーされる)、コマンドは終了します。
- `--monitor` 付きの場合、コマンドは継続して動作し、ファイルが変更されるたびに処理を行います。停止するには Ctrl+C を押してください。
- `--monitor` は、`--json`、`--mode`、`--conf-maker-web`、`--conf-maker-cli` のいずれにも追加できます。
- json ファイル内では、代わりに `"monitor": true` と記述します。`--monitor` と `"monitor": true` のいずれかが指定されれば、監視が継続します。

```bash
ml_writing_helper --mode doc_conv --src docs --dst docs_out            # 1 回変換して終了
ml_writing_helper --mode doc_conv --src docs --dst docs_out --monitor  # 監視を継続
ml_writing_helper --json --monitor                                     # ./ml_writing_helper.json からのタスク、監視を継続
```

#### json ファイルの作成 (`--conf-maker-web` / `--conf-maker-cli`)

- `--conf-maker-web`: ブラウザにフォームを開きます。タスクを追加し、プレビューを確認したのち、「保存して実行」または「保存のみ」を押します。「monitor」のチェックボックスで、json ファイル内の `"monitor"` が設定されます。
- `--conf-maker-cli`: 各設定をターミナルで質問します。既定値 ([ ] 内に表示) を受け入れるには Enter を押してください。無効な入力 (例: 存在しないフォルダー) は再度質問されます。保存後、すぐにタスクを実行できます。
- ファイルがすでに存在する場合、その内容は初期値として読み込まれ、保存すると上書きされます。
- PATH がフォルダーの場合、その中に `ml_writing_helper.json` が作成されます。

#### json 指示

`--json` は、json ファイルのパスまたは JSON 文字列のいずれかを受け取ります:

- 値が `{` で始まる場合、JSON 文字列として解析され、タスク指示として実行されます。
- それ以外の場合、json ファイルのパスとして扱われます。
- 値なしの場合 (`ml_writing_helper --json`)、`./ml_writing_helper.json` が使用されます。

1 つのファイル内に複数のタスクを定義できます。相対パスは `root` から解決され、`root` は json ファイルのディレクトリから解決されます (JSON 文字列の場合は、カレントディレクトリから解決されます)。

```json
{
  "root": ".",
  "observer": "polling",
  "sleep_sec": 1.0,
  "log_level": "INFO",
  "monitor": true,
  "tasks": [
    {"type": "img_conv", "src": "fig_src", "dst": "fig_gen", "ext": "pdf", "gray": true, "crop": true},
    {"type": "img_conv", "src": "slides", "dst": "fig_gen", "ext": "eps"},
    {"type": "copy", "src": "~/Documents/BibTexExported", "dst": "bib", "exts": ["bib"], "diff_sec": 10},
    {"type": "doc_conv", "src": "docs", "dst": "docs_out", "ext": ["pdf", "html"]}
  ]
}
```

| タスクキー     | 型                               | 既定値          | 説明                                                                         |
| -------------- | -------------------------------- | --------------- | ---------------------------------------------------------------------------- |
| `type`         | `img_conv` / `copy` / `doc_conv` | 必須            | タスクの種類                                                                 |
| `src`, `dst`   | パス                             | 必須            | 監視対象ディレクトリ / 出力ディレクトリ (`dst` は存在しなければ作成されます) |
| `ext`          | 文字列                           | `pdf`           | `img_conv` のみ。eps, pdf, png, jpg, jpeg, gif, bmp, tiff                    |
| `gray`, `crop` | 真偽値                           | `false`, `true` | `img_conv` のみ                                                              |
| `exts`         | リスト                           | `["bib"]`       | `copy` のみ。コピー対象の拡張子                                              |
| `diff_sec`     | 整数                             | `10`            | `copy` のみ。src/dst のタイムスタンプの差がこの秒数以下ならスキップ          |

- `doc_conv` のキーについては、[モード: doc_conv](#モード-doc_conv) を参照してください。
- `mode` を `type` の代わりに使用できます (CLI のモードと同じ意味)。
- `copy` タスクでは、`ext` を `exts` の代わりに使用できます (文字列またはリスト)。

##### JSON 文字列 (`--json '{...}'`)

json ファイルと同じ形式です。1 つのタスクは、`mode` (短縮形) を用いてトップレベルに記述することもできます:

```bash
# 1 つのタスク (短縮形)
ml_writing_helper --json '{"mode": "copy", "src": "~/Documents/BibTexExported", "dst": "bib", "ext": "bib"}'

# 複数のタスク (json ファイルと同じ形式)
ml_writing_helper --json '{"tasks": [{"mode": "img_conv", "src": "fig_src", "dst": "fig_gen", "ext": "pdf"}, {"mode": "copy", "src": "~/Documents/BibTexExported", "dst": "bib"}]}'
```

トップレベルの `monitor` (真偽値、既定 `false`): `true` にすると変更の監視を継続し、`false` にするとすべてのタスクを 1 回だけ実行して終了します。

JSON 文字列は、シェルがダブルクォートを変換せずに渡せるように、シングルクォート `'...'` で囲んでください。

#### CLI 指示 (`--mode`)

```bash
ml_writing_helper --mode [img_conv|copy|doc_conv] [サブパラメータ...] [--root [ルートパス]]

# fig_src/ -> fig_gen/ をグレースケールの .pdf として
ml_writing_helper --mode img_conv --ext pdf --gray

# エクスポートした .bib を bib/ にコピー
ml_writing_helper --mode copy --src ~/Documents/BibTexExported --dst bib

# docs/**/*.md -> docs_out/**/*.pdf と .html
ml_writing_helper --mode doc_conv --src docs --dst docs_out --ext pdf --ext html
```

##### 共通パラメータ

すべてのモードで利用可能 (例: `ml_writing_helper --mode copy --src a --dst b --log-level DEBUG`)。

| オプション         | 既定値                  | 説明                                                                                            |
| ------------------ | ----------------------- | ----------------------------------------------------------------------------------------------- |
| `--observer`       | `polling`               | watchdog のバックエンド (`polling` はクラウドストレージ向け、`native` は軽量)                   |
| `--sleep-sec`      | `1.0`                   | メインループのスリープ時間                                                                      |
| `--diff-sec`       | `10`                    | src/dst のタイムスタンプの差がこの秒数以下ならスキップ                                          |
| `--log-level`      | `INFO`                  | コンソールのログレベル                                                                          |
| `--root root_PATH` | カレントフォルダー(".") | このアプリが相対パスを理解するための基準 PATH                                                   |
| `--monitor`        | オフ                    | 変更の監視を継続。なしの場合、1 回だけ実行して終了 (`--json` / `--conf-maker-*` との併用も可能) |


##### モード: img_conv

このモードは、src パスの画像 (例: .pptx, .png) を、指定の形式 (例: .eps, .pdf) で dst パスへ変換します。

| オプション  | 既定値    | 説明                                                  |
| ----------- | --------- | ----------------------------------------------------- |
| `--src DIR` | `fig_src` | 図表のソースディレクトリ。1 回のみ                    |
| `--dst DIR` | `fig_gen` | 図表の出力ディレクトリ (存在しなければ作成)。1 回のみ |
| `--ext FMT` | `pdf`     | 出力形式: eps, pdf, png, jpg, jpeg, gif, bmp, tiff    |
| `--gray`    | オフ      | グレースケールに変換                                  |
| `--no-crop` | オフ      | 切り抜き (トリミング) を無効にする                    |

##### モード: copy

このモードは、src パスのファイルを dst パスへコピーします。

| オプション  | 既定値 | 説明                                                                                                                            |
| ----------- | ------ | ------------------------------------------------------------------------------------------------------------------------------- |
| `--src SRC` | (必須) | SRC から変更されたファイルをコピー。繰り返し指定可                                                                              |
| `--dst DST` | (必須) | 変更されたファイルを DST にコピー。繰り返し指定可: `--src` と順序でペアになるか、1 つの `--dst` にすべての `--src` が集約される |
| `--ext EXT` | `bib`  | コピー対象の拡張子。繰り返し指定可                                                                                              |

`--src` と `--dst` を複数回指定した場合は、次のように対応付けられます:

- 両方の個数が同じ場合、指定された順序でペアになります (例: `--src a --dst x --src b --dst y` で a→x と b→y をコピー)。
- `--dst` が 1 つのみ指定された場合、すべての `--src` がそこへコピーされます。
- その他の個数の組み合わせはエラーになります。


##### モード: doc_conv

このモードは、src 配下のドキュメント (`.md`、`.html`、サブフォルダー込み) が変更されたときに PDF / HTML / DOCX へ変換します。
src 配下のフォルダ構造は dst にも再現されます。

| オプション     | 既定値         | 説明                                                                                           |
| -------------- | -------------- | ---------------------------------------------------------------------------------------------- |
| `--src DIR`    | `.`            | ドキュメントのソースディレクトリ (サブフォルダー込み)。1 回のみ                                |
| `--dst DIR`    | `--src` と同じ | 出力ディレクトリ (存在しなければ作成)。1 回のみ                                                |
| `--ext FMT`    | `pdf`          | 出力形式: pdf, html, docx。繰り返し指定可 (例: `--ext pdf --ext html`)                         |
| `--engine`     | `auto`         | `auto` / `pandoc` / `playwright` / `marp` / `slidev` (下記参照)                                |
| `--pattern`    | `*.md`         | 変換対象のファイル名。`*` は任意の文字にマッチ。繰り返し指定可 (例: `"*_marp.md"`, `"*.html"`) |
| `--header TEX` | 日本語ヘッダー | PDF 変換のため pandoc に渡す TeX ヘッダーファイル。繰り返し指定可                              |

json タスクのキー (`"type": "doc_conv"`):

| タスクキー    | 型              | 既定値         | 説明                                                                              |
| ------------- | --------------- | -------------- | --------------------------------------------------------------------------------- |
| `src`         | パス            | 必須           | 監視対象ディレクトリ (サブフォルダー込み)                                         |
| `dst`         | パス            | `src` と同じ   | 出力ディレクトリ                                                                  |
| `ext`         | 文字列 / リスト | `"pdf"`        | pdf, html, docx                                                                   |
| `engine`      | 文字列          | `"auto"`       | auto, pandoc, playwright, marp, slidev                                            |
| `pattern`     | 文字列 / リスト | `"*.md"`       | 変換対象のファイル名                                                              |
| `header`      | パス / リスト   | 日本語ヘッダー | pandoc PDF 用の TeX ヘッダーファイル                                              |
| `marp_header` | パス / リスト   | なし           | Marp の frontmatter に追加される YAML フラグメントファイル                        |
| `copy_exts`   | リスト          | なし           | dst へそのままコピーする拡張子 (例: HTML から参照される画像用 `[ "png", "jpg" ]`) |
| `diff_sec`    | 整数            | `10`           | 起動時、src が出力よりこの秒数分以上新しい場合のみ変換                            |

`engine: auto` は、ファイルごとにコンバーターを選択します:

| ファイル                                          | pdf                  | html           | docx   |
| ------------------------------------------------- | -------------------- | -------------- | ------ |
| Marp (frontmatter に `marp: true`)                | marp                 | marp           | pandoc |
| Slidev (frontmatter に `theme:` / `layout:` など) | slidev               | ブラウザ HTML  | pandoc |
| ` ```mermaid ` / ` ```plantuml ` ブロックを含む   | playwright           | ブラウザ HTML  | pandoc |
| その他                                            | pandoc (lualatex)    | ブラウザ HTML  | pandoc |
| `.html` (`--pattern "*.html"` の場合)             | Chrome headless 印刷 | そのままコピー | pandoc |

- 「ブラウザ HTML」は marked.js / mermaid.js / highlight.js / KaTeX を CDN から埋め込むため、表示にはインターネット接続が必要です。
- dst が src の内部にある場合、dst 内のファイルは再変換されません。隠しファイル/フォルダーと `node_modules` はスキップされます。
- 監視中、ファイルがその出力より新しいときにのみ変換されます。
- ツールが不足している場合は、警告が表示され、可能な限り pandoc が代わりに使用されます。

doc_conv の必要条件 (使用する分のみ):

- pandoc + LuaLaTeX (PDF): `brew install pandoc` と `brew install --cask mactex-no-gui` / `sudo apt-get install pandoc texlive-luatex texlive-lang-japanese`
- playwright (PDF 内の mermaid / PlantUML): `pipx inject ml_writing_helper playwright` (または `pip install "ml_writing_helper[doc]"`) のち `playwright install chromium`。Chromium が不足している場合、初回使用時に自動でインストールされます。
- PlantUML: `brew install plantuml`
- Marp: `npm install -g @marp-team/marp-cli` (または `npx` が使用されます)
- Slidev: `npm install -g @slidev/cli` (または `npx` が使用されます)
- Chrome / Chromium (`.html` → PDF)


### 単一ファイル変換 (レガシーサブコマンド)

- `ml_writing_helper convert src_path dst_dir to_fmt [--gray] [--no-crop]`
- サブコマンド名は省略可能: `ml_writing_helper src_path dst_dir to_fmt` (かつての `convert4ml` と同じ)
- `ml_writing_helper monitor src_dir dst_dir to_fmt` は 1 つのフォルダーを監視し、`--monitor` なしで監視を継続します

## インストール


必要条件をインストールしてください。
1. LibreOffice
    1. Windows 10 以降: `winget install LibreOffice`
    2. MacOS: `brew install --cask libreoffice`
    3. Linux: `sudo apt-get install libreoffice`
    4. 手動インストール...
2. poppler (pdf2image で使用): `brew install poppler` / `sudo apt-get install poppler-utils`
3. このパッケージ (pipx 推奨):
    1. ローカルチェックアウトから: `pipx install .` (更新: `pipx install --force .`)
    2. ビルド済み wheel から: `pipx install dist/ml_writing_helper-<ver>-<tag>.whl`
    3. GitHub から: `pipx install git+https://github.com/HirotsuguMINOWA/ml_writing_helper.git`


## 使い方

![usage instruction gif](attachment/usage70.gif)

### 準備

- サポート用のルールファイルを作成します。
  - このコードを、例えば `start_watcher.py` として保存してください。
1. `python [以下のコード]`
    ```python
    from ml_writing_helper import Monitor
    from pathlib import Path
    manu_path = Path(__file__).resolve().parent # manuscript_path as hiro_watcher
    o=Monitor()

    # Convert .pptx in fig_src dir TO fig_gen dir.
    o.set_monitor(
     src_dir=manu_path.joinpath("fig_src")
     ,dst_dir=manu_path.joinpath("fig_gen")
     ,to_fmt=".eps" # .png, .pdf and so on.
    )

    # Copy document manager(mendeley/zotero...) exported .bib is copied to manu_path
    o.set_monitor(
      src_dir="/usr/<username>/Documents/BibTexExported"
      ,dst_dir=manu_path
      ,to_fmt=".bib"
    )

    o.start_monitors()
    ```
    
### ターミナルからの使用例
1. このパッケージをインストールします。
2. `python start_watcher.py`
  
### Visual Studio SCode(VSC) からの使用例
1. セットアップ
    1. VSC にプラグイン "CodeRunner(`formulahendry.code-runner`)" をインストールします。
2. 設定
    1. `.vscode/settings.json` で python インタープリターパスを設定
       - `.vscode/settings.json`
         ```json
         {
           "code-runner.executorMap": {
             "python": "/Users/YOUR_USER_ID/pyenv/ml_writing_helper/bin/python",
           }
         }
         ```
3. ルールファイル `start_watcher.py` を実行
    1. 'Cmd(Ctrl)+Opt(Alt)+N' で `start_watcher.py` を実行
    2. または `philfontaine.autolaunch` と組み合わせれば自動実行?

# トラブルシューティング / ヒント

## LaTeX では pdf より eps を優先

- 理由: 適切なサイズで表示されるため
- pdf では `\linewidth` が (複数カラムの) 幅に正しく収まらないことがあります。おそらく pdf のサイズが正しく取得できていないためです。
  - png と比べると、eps や .xbb はサイズを指定するために bounding box が不要なため使いやすいです。
  - IEICE テンプレートでは、上記のサイズ取得失敗が原因で、画像が通常は画像として出力されるべきところをテキストに埋もれてしまうことがあるようです。

## **切り抜き (白余白の除去) が失敗した**

### 原因

1. 対象画像に見えない枠がある

## スライドから画像への変換が失敗した

### 原因

1. 形式として `pdf` を使っている場合は、**`.png`** に変更してください。
    1. 現行バージョンでは pdf ファイルの切り抜きが失敗します。

## PowerPoint ファイルから画像 (PDF 含む) への変換で画質が低い

1. MacOS: LibreOfficeVanilla が検証されていない?
    1. このエディションでは変換機能が削除されています。
2. その .pttx を LibreOffice で開いたときに画質が低下していないか?
    1. PowerPoint では画質が低下していても、LibreOffice で開いたときに画質が低下する可能性があります。ドキュメントを作り直すことで解決できることがあります。
    2. PowerPoint ファイルは、PowerPoint 上で PNG に変換してから、このスクリプトで eps に変換できます。
3. MacOS: LibreOffice アプリケーションの検証が完了していない?
    1. Homebrew からインストールした後、アプリケーションの検証を完了せずに LibreOffice を使用すると、画質が低くなります。

