from __future__ import annotations

import html
import json
import re
import uuid
import zipfile
from pathlib import Path
from xml.sax.saxutils import escape


class Scorm12Error(ValueError):
    """Raised when a Markdown quiz does not follow the supported format."""


_QUESTION_HEADING = re.compile(r"^##\s+(.+?)\s*$")
_TITLE_HEADING = re.compile(r"^#\s+(.+?)\s*$")
_OPTION = re.compile(r"^\s*[-*+]\s+\[([ xX])\]\s+([A-Z])(?:[.)])\s+(.+?)\s*$")
_CHECKBOX = re.compile(r"^\s*[-*+]\s+\[")


def _render_inline(text: str) -> str:
    rendered = html.escape(text, quote=True)
    rendered = re.sub(r"`([^`]+)`", r"<code>\1</code>", rendered)
    rendered = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", rendered)
    rendered = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<em>\1</em>", rendered)
    return rendered


def _render_markdown(lines: list[str]) -> str:
    paragraphs: list[str] = []
    current: list[str] = []
    for line in lines:
        if line.strip():
            current.append(_render_inline(line.strip()))
        elif current:
            paragraphs.append("<p>" + "<br>\n".join(current) + "</p>")
            current = []
    if current:
        paragraphs.append("<p>" + "<br>\n".join(current) + "</p>")
    return "\n".join(paragraphs)


def parse_quiz(markdown_text: str, fallback_title: str = "Quiz") -> dict[str, object]:
    """Parse a single-choice quiz from H2 question headings and labeled checkboxes."""
    title = fallback_title
    questions: list[dict[str, object]] = []
    current: dict[str, object] | None = None
    body: list[str] = []
    options: list[dict[str, object]] = []

    def finish_question() -> None:
        nonlocal body, options, current
        if current is None:
            return
        if len(options) < 2:
            raise Scorm12Error(f"問題「{current['title']}」には選択肢が2つ以上必要です")
        correct = [option for option in options if option["correct"]]
        if len(correct) != 1:
            raise Scorm12Error(f"問題「{current['title']}」の正解は1つだけ指定してください")
        labels = [str(option["label"]) for option in options]
        if len(labels) != len(set(labels)):
            raise Scorm12Error(f"問題「{current['title']}」の選択肢ラベルが重複しています")
        current["prompt"] = _render_markdown(body)
        current["options"] = options
        current["answer"] = str(correct[0]["label"])
        questions.append(current)
        body = []
        options = []

    for line_number, line in enumerate(markdown_text.splitlines(), start=1):
        title_match = _TITLE_HEADING.match(line)
        if title_match and current is None:
            title = title_match.group(1)
            continue
        question_match = _QUESTION_HEADING.match(line)
        if question_match:
            finish_question()
            current = {"title": question_match.group(1)}
            continue
        if current is None:
            continue
        option_match = _OPTION.match(line)
        if option_match:
            options.append({
                "correct": option_match.group(1).strip().lower() == "x",
                "label": option_match.group(2),
                "text": option_match.group(3),
            })
        elif _CHECKBOX.match(line):
            raise Scorm12Error(f"{line_number}行目: 選択肢は '- [ ] A. 内容' の形式で記述してください")
        else:
            body.append(line)

    finish_question()
    if not questions:
        raise Scorm12Error("問題がありません。問題は '## 問題文' の見出しで開始してください")
    return {"title": title, "questions": questions}


def _build_html(quiz: dict[str, object]) -> str:
    data = json.dumps(quiz, ensure_ascii=False).replace("<", "\\u003c").replace("&", "\\u0026")
    return '''<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>''' + html.escape(str(quiz["title"])) + '''</title>
<style>
body{font:16px/1.65 system-ui,sans-serif;max-width:850px;margin:2rem auto;padding:0 1rem;color:#202a33}
h1{font-size:1.6rem;border-bottom:2px solid #167d78;padding-bottom:.5rem}
fieldset{border:1px solid #aab7b6;border-radius:4px;margin:1.5rem 0;padding:1rem}
legend{font-weight:700;padding:0 .4rem}.choice{display:block;padding:.35rem .5rem}
button{font:inherit;padding:.55rem 1.2rem;background:#167d78;color:white;border:0;border-radius:3px;cursor:pointer}
#result{font-weight:700;margin:1rem 0}.correct{color:#176b3a}.incorrect{color:#a22}
</style>
</head>
<body>
<h1>''' + html.escape(str(quiz["title"])) + '''</h1>
<form id="quiz"></form>
<button id="submit" type="button">回答する</button>
<p id="result" role="status" aria-live="polite"></p>
<script id="quiz-data" type="application/json">''' + data + '''</script>
<script>
(() => {
  const quiz = JSON.parse(document.getElementById('quiz-data').textContent);
  const form = document.getElementById('quiz');
  const result = document.getElementById('result');
  const questionStartedAt = [];
  let api = null;
  let initialized = false;
  let submitted = false;
  function findApi(win) {
    for (let depth = 0; win && depth < 10; depth++) {
      try {
        if (win.API) return win.API;
        if (win === win.parent) break;
        win = win.parent;
      } catch (_) {
        break;
      }
    }
    try { if (window.opener && window.opener.API) return window.opener.API; } catch (_) {}
    return null;
  }
  function setValue(key, value) {
    if (initialized && api) api.LMSSetValue(key, String(value));
  }
  function commit() {
    if (initialized && api) api.LMSCommit('');
  }
  function latency(elapsedMs) {
    const elapsedSeconds = elapsedMs / 1000;
    const hours = Math.floor(elapsedSeconds / 3600);
    const minutes = Math.floor(elapsedSeconds % 3600 / 60);
    const seconds = elapsedSeconds % 60;
    return String(hours).padStart(4, '0') + ':' + String(minutes).padStart(2, '0') + ':' + seconds.toFixed(2).padStart(5, '0');
  }
  api = findApi(window);
  if (api) initialized = api.LMSInitialize('') === 'true';
  if (initialized) setValue('cmi.core.lesson_status', 'incomplete');
  quiz.questions.forEach((question, index) => {
    questionStartedAt[index] = Date.now();
    const fieldset = document.createElement('fieldset');
    const legend = document.createElement('legend');
    legend.textContent = (index + 1) + '. ' + question.title;
    fieldset.appendChild(legend);
    if (question.prompt) {
      const prompt = document.createElement('div');
      prompt.innerHTML = question.prompt;
      fieldset.appendChild(prompt);
    }
    question.options.forEach(option => {
      const label = document.createElement('label');
      label.className = 'choice';
      const input = document.createElement('input');
      input.type = 'radio'; input.name = 'q' + index; input.value = option.label;
      label.append(input, document.createTextNode(' ' + option.label + '. ' + option.text));
      fieldset.appendChild(label);
    });
    form.appendChild(fieldset);
  });
  document.getElementById('submit').addEventListener('click', () => {
    if (submitted) return;
    const answers = quiz.questions.map((_, index) => form.querySelector('input[name="q' + index + '"]:checked'));
    if (answers.some(answer => !answer)) {
      result.textContent = 'すべての問題に回答してください。'; result.className = 'incorrect'; return;
    }
    submitted = true;
    let correctCount = 0;
    quiz.questions.forEach((question, index) => {
      const answer = answers[index].value;
      const correct = answer === question.answer;
      if (correct) correctCount++;
      const prefix = 'cmi.interactions.' + index + '.';
      setValue(prefix + 'id', 'q' + (index + 1));
      setValue(prefix + 'type', 'choice');
      setValue(prefix + 'weighting', 1);
      setValue(prefix + 'student_response', answer);
      setValue(prefix + 'result', correct ? 'correct' : 'wrong');
      setValue(prefix + 'latency', latency(Date.now() - questionStartedAt[index]));
    });
    const score = Math.round(correctCount / quiz.questions.length * 100);
    setValue('cmi.core.score.raw', score);
    setValue('cmi.core.lesson_status', 'completed');
    commit();
    result.textContent = '得点: ' + score + '% (' + correctCount + '/' + quiz.questions.length + ')';
    result.className = score === 100 ? 'correct' : '';
    document.getElementById('submit').disabled = true;
  });
  window.addEventListener('beforeunload', () => {
    commit();
    if (initialized && api) api.LMSFinish('');
  });
})();
</script>
</body>
</html>
'''


def build_scorm12_package(source_path: Path, output_path: Path) -> Path:
    """Create a SCORM 1.2 ZIP package from a Markdown single-choice quiz."""
    try:
        markdown_text = source_path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        raise Scorm12Error(f"入力ファイルを読み込めません: {exc}") from exc
    quiz = parse_quiz(markdown_text, fallback_title=source_path.stem)
    identifier = f"quiz-{uuid.uuid4().hex}"
    title = escape(str(quiz["title"]))
    manifest = f'''<?xml version="1.0" encoding="UTF-8"?>
<manifest identifier="{identifier}" version="1.0"
 xmlns="http://www.imsproject.org/xsd/imscp_rootv1p1p2"
 xmlns:adlcp="http://www.adlnet.org/xsd/adlcp_rootv1p2"
 xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
 xsi:schemaLocation="http://www.imsproject.org/xsd/imscp_rootv1p1p2 imscp_rootv1p1p2.xsd http://www.adlnet.org/xsd/adlcp_rootv1p2 adlcp_rootv1p2.xsd">
  <metadata><schema>ADL SCORM</schema><schemaversion>1.2</schemaversion></metadata>
  <organizations default="org-1">
    <organization identifier="org-1"><title>{title}</title>
      <item identifier="item-1" identifierref="resource-1"><title>{title}</title></item>
    </organization>
  </organizations>
  <resources>
    <resource identifier="resource-1" type="webcontent" adlcp:scormtype="sco" href="index.html">
      <file href="index.html" />
    </resource>
  </resources>
</manifest>
'''
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as package:
        package.writestr("imsmanifest.xml", manifest)
        package.writestr("index.html", _build_html(quiz))
    return output_path