"""Update Epic plan wording and export the user's table layout to Word.

Run with: streamlit run app.py
Requires Streamlit and python-docx. Note text stays in the current session.
"""

from base64 import b64decode
from copy import deepcopy
from dataclasses import dataclass
from html import escape
from io import BytesIO
import re


PHRASES = ("Continue", "Will continue", "We will continue", "We shall continue")
CUSTOM = "Custom phrase"
FULL_NOTE = "Assessment, indications, and plan"
PLAN_ONLY = "Plan only"
WORD_FORMAT_VERSION = 2

_INDICATIONS = (
    r"(?:CLINICAL\s+)?INDICATIONS\s+FOR\s+"
    r"(?:CRITICAL\s+CARE(?:\s+SERVICES)?"
    r"(?:\s+(?:OR|AND)\s+HOSPITAL\s+CARE(?:\s+SERVICES)?)?"
    r"|(?:CONTINUED\s+)?HOSPITALIZATION"
    r"|HOSPITAL\s+(?:CARE(?:\s+SERVICES)?|SERVICES|ADMISSION))"
)
_EXCLUDED = (
    r"PATIENT\s+(?:INFORMATION|INFO)|DIAGNOSES|SUBJECTIVE|OBJECTIVE"
    r"|INTERVAL\s+EVENTS|OVERNIGHT\s+EVENTS|REVIEW\s+OF\s+SYSTEMS|ROS"
    r"|PHYSICAL\s+EXAM(?:INATION)?|PE|VITAL\s+SIGNS"
    r"|ATTESTATION|CRITICAL\s+CARE\s+TIME|TIME\s+SPENT"
)
_HEADINGS = re.compile(
    rf"^(?P<label>ASSESSMENT|PLAN|{_INDICATIONS}|CLINICAL\s+INDICATIONS|{_EXCLUDED})"
    r"\s*(?::\s*(?P<body>.*))?$",
    re.IGNORECASE,
)
_INDICATIONS_TOKEN = re.compile(r"^\{CKCLININDICATIONS:[^}]+\}$", re.IGNORECASE)
_LIST_MARKER = r"(?:\d+(?:\)\.?|[.)])|\(\d+\)|[a-zA-Z][.)]|[-\u2022\u25cf\u25aa\u2023])"
_MARKER_ONLY = re.compile(rf"^{_LIST_MARKER}$")


@dataclass(frozen=True)
class NoteResult:
    text: str
    replacements: int
    sections: tuple


def normalize_pasted_text(text):
    """Turn table cell separators into lines, retaining clinical text and lists."""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = text.replace("\u00a0", " ")
    for separator in ("\x07", "\x0b", "\x0c", "\u2028", "\u2029"):
        text = text.replace(separator, "\n")

    lines = []
    for raw_line in text.split("\n"):
        if not raw_line.strip():
            lines.append("")
            continue
        # A clipboard table can use tabs for cells or for list-number spacing.
        cells = [cell.strip() for cell in raw_line.split("\t") if cell.strip()]
        for cell in cells:
            if lines and _MARKER_ONLY.fullmatch(lines[-1]):
                lines[-1] += " " + cell
            else:
                lines.append(cell)
    return "\n".join(lines).strip()


def identify_heading(line):
    """Classify explicit note headings without guessing from diagnoses."""
    candidate = line.strip()
    if _INDICATIONS_TOKEN.fullmatch(candidate):
        return "indications"
    # Accept Markdown-wrapped headings while leaving their source text intact.
    candidate = re.sub(r"^#{1,6}\s+", "", candidate)
    candidate = re.sub(r"^(\*\*|__)(.+?)\1", r"\2", candidate)
    match = _HEADINGS.fullmatch(candidate)
    if not match:
        return None
    label = re.sub(r"\s+", " ", match.group("label")).upper()
    if label == "ASSESSMENT":
        return "assessment"
    if label == "PLAN":
        return "plan"
    if "INDICATIONS" in label:
        return "indications"
    return "excluded"


def _phrase_pattern(phrase):
    return r"[ \t]+".join(re.escape(word) for word in phrase.split())


def replace_plan_starters(text, source_phrase, replacement_phrase):
    """Replace instruction starters, not words inside other clinical sentences."""
    if source_phrase.casefold() == replacement_phrase.casefold():
        return text, 0
    source = _phrase_pattern(source_phrase)
    target = re.compile(_phrase_pattern(replacement_phrase) + r"(?!\w)", re.IGNORECASE)
    starter = re.compile(
        r"(?P<prefix>(?:^|(?<=[.!?:;])[ \t]+)[ \t]*"
        rf"(?:{_LIST_MARKER}[ \t]*)*(?:[\"\u201c])?)"
        rf"(?P<phrase>{source})(?!\w)",
        re.IGNORECASE,
    )
    replacements = 0

    def substitute(match):
        nonlocal replacements
        # Also makes custom replacements such as 'Continue with' idempotent.
        if target.match(text, match.start("phrase")):
            return match.group(0)
        replacements += 1
        return match.group("prefix") + replacement_phrase

    return starter.sub(substitute, text), replacements


def update_note(raw_text, source_phrase="Continue", replacement_phrase="Will continue", input_mode=FULL_NOTE):
    """Keep assessment/indications/plan and change only plan instruction wording.

    A full-note paste needs a separate PLAN heading. Plan-only input is explicit
    so an unrecognized full note is never silently treated as a plan.
    """
    if not isinstance(raw_text, str) or not raw_text.strip():
        raise ValueError("Paste the note you want to update.")
    for phrase in (source_phrase, replacement_phrase):
        if not isinstance(phrase, str) or not phrase.strip():
            raise ValueError("Enter both the phrase to find and its replacement.")
        if "\n" in phrase or "\r" in phrase or "\t" in phrase:
            raise ValueError("Each wording choice must be a single phrase on one line.")
    if input_mode not in (FULL_NOTE, PLAN_ONLY):
        raise ValueError("Choose the full note or plan-only input option.")

    source_phrase = source_phrase.strip()
    replacement_phrase = replacement_phrase.strip()
    lines = normalize_pasted_text(raw_text).split("\n")
    has_plan_heading = any(identify_heading(line) == "plan" for line in lines)
    if input_mode == FULL_NOTE and not has_plan_heading:
        raise ValueError(
            "A separate PLAN heading was not found. Include that heading when "
            "pasting the note, or select Plan only if you pasted just the plan."
        )
    if input_mode == PLAN_ONLY and not has_plan_heading:
        lines = ["PLAN", ""] + lines

    output = []
    sections = []
    current_section = None
    replacements = 0
    for line in lines:
        heading = identify_heading(line)
        if heading:
            current_section = None if heading == "excluded" else heading
            if current_section and current_section not in sections:
                sections.append(current_section)
        if current_section is None:
            continue
        if current_section == "plan":
            # A heading may have its first instruction on the same line.
            line, changed = replace_plan_starters(line, source_phrase, replacement_phrase)
            replacements += changed
        output.append(line)

    result = re.sub(r"\n{3,}", "\n\n", "\n".join(output)).strip()
    if not result:
        raise ValueError("No assessment, clinical indications, or plan text was found.")
    return NoteResult(result, replacements, tuple(sections))



_WORD_TEMPLATE = (
    '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'
)

_WORD_LIST_START = re.compile(r"^\s*(?:\d+(?:\)\.?|[.)])|\(\d+\)|[a-zA-Z][.)]|[-\u2022\u25cf\u25aa\u2023])\s*")
_WORD_LIST_FIRST = re.compile(r"^\s*(?:1(?:\)\.?|[.)])|\(1\)|[-\u2022\u25cf\u25aa\u2023])\s*")
_WORD_STANDARD_ACTIONS = ("Continue", "Will continue", "We will continue", "We shall continue")


def _word_action_pattern(action_phrases):
    if isinstance(action_phrases, str):
        action_phrases = (action_phrases,)
    choices = _WORD_STANDARD_ACTIONS + tuple(action_phrases or ())
    patterns = [
        r"[ \t]+".join(re.escape(word) for word in phrase.split())
        for phrase in choices if isinstance(phrase, str) and phrase.strip()
    ]
    return re.compile(r"^(?:" + "|".join(patterns) + r")(?!\w)", re.IGNORECASE)


def _word_trim_lines(lines):
    lines = list(lines)
    while lines and not lines[0].strip():
        lines.pop(0)
    while lines and not lines[-1].strip():
        lines.pop()
    return lines


def _word_heading_parts(line):
    """Separate an inline section heading from its narrative, without rewriting it."""
    if line.strip().startswith("{"):
        return "", line.strip()
    match = re.match(r"^(.*?:)\s*(.*)$", line)
    if match:
        return match.group(1), match.group(2)
    return line, ""


def _word_plan_blocks(lines, action_phrases=()):
    """Infer the fixed diagnosis-header/numbered-plan pattern conservatively.

    Every input line is retained. Text without a recognizable diagnosis header
    goes into an unlabelled plan row rather than being discarded or renamed.
    """
    blocks = []
    heading = []
    body = []
    action_pattern = _word_action_pattern(action_phrases)

    def flush():
        nonlocal heading, body
        if heading or any(line.strip() for line in body):
            blocks.append({
                "kind": "diagnosis" if heading else "plan_body",
                "heading": "\n".join(heading),
                "lines": _word_trim_lines(body),
            })
        heading, body = [], []

    for index, line in enumerate(lines):
        text = line.strip()
        following = next((value.strip() for value in lines[index + 1:] if value.strip()), "")
        is_list = bool(_WORD_LIST_START.match(text))
        is_placeholder = bool(re.fullmatch(r"\*{3,}", text))
        is_upper = any(char.isalpha() for char in text) and text.upper() == text
        before_first_item = bool(_WORD_LIST_FIRST.match(following))
        before_action = bool(action_pattern.match(following))
        previous = lines[index - 1].strip() if index else ""
        # A wrapped continuation such as 'as needed' is not a new diagnosis.
        # Mixed-case headings need a real group boundary as well as plan text.
        group_boundary = (
            index == 0
            or not previous
            or (bool(_WORD_LIST_START.match(previous)) and before_first_item)
        )
        title_shaped = (
            bool(text) and text[0].isupper()
            and len(text) <= 240
            and not text.endswith((".", ";", "?", "!"))
        )
        header_like = (
            bool(text)
            and not is_list
            and not action_pattern.match(text)
            and (
                is_placeholder
                or (is_upper and not text.endswith((".", ";", "?", "!")))
                or (group_boundary and title_shaped and (before_first_item or before_action))
            )
        )
        if header_like:
            # Clipboard wrapping may split one long diagnosis across two lines.
            if heading and is_upper and previous and not any(value.strip() for value in body):
                heading.append(line)
            else:
                flush()
                heading = [line]
        else:
            body.append(line)
    flush()
    return blocks


def note_table_blocks(note_text, action_phrases=()):
    """Describe the retained note as ordered, editable Word layout blocks."""
    if not isinstance(note_text, str) or not note_text.strip():
        raise ValueError("There is no updated note to export.")
    blocks = []
    kind, heading, lines = None, "", []

    def flush():
        nonlocal lines
        kept_lines = _word_trim_lines(lines)
        if kind == "plan":
            blocks.append({"kind": "plan_heading", "heading": heading, "lines": []})
            blocks.extend(_word_plan_blocks(kept_lines, action_phrases=action_phrases))
        elif kind is not None and (heading or kept_lines):
            blocks.append({"kind": kind, "heading": heading, "lines": kept_lines})
        elif kept_lines:
            blocks.append({"kind": "plan_body", "heading": "", "lines": kept_lines})
        lines = []

    for line in note_text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        section = identify_heading(line)
        if section in ("assessment", "indications", "plan"):
            flush()
            kind = section
            heading, inline = _word_heading_parts(line)
            if inline:
                lines.append(inline)
        else:
            lines.append(line)
    flush()
    return blocks


def build_word_note(note_text, action_phrases=()):
    """Return a DOCX using the supplied note's table, font and page formatting."""
    from docx import Document
    from docx.oxml.ns import qn
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    document = Document(BytesIO(b64decode(_WORD_TEMPLATE)))
    prototypes = [deepcopy(table._tbl) for table in document.tables]
    spacer = deepcopy(document.paragraphs[0]._p)
    narrative = deepcopy(document.paragraphs[1]._p)
    body = document._element.body
    for child in list(body):
        if child.tag != qn("w:sectPr"):
            body.remove(child)
    body.insert_element_before(deepcopy(spacer), "w:sectPr")

    def fill_paragraph(element, text, bold=None, keep_next=False):
        paragraph = Paragraph(element, document)
        first_rpr = None
        if paragraph.runs and paragraph.runs[0]._r.rPr is not None:
            first_rpr = deepcopy(paragraph.runs[0]._r.rPr)
        paragraph.clear()
        run = paragraph.add_run(text)
        if first_rpr is not None:
            run._r.insert(0, first_rpr)
        if bold is not None:
            run.bold = bold
        if keep_next:
            paragraph.paragraph_format.keep_with_next = True
        return paragraph

    def fill_cell(cell, values, is_heading=False):
        prototype = deepcopy(cell.paragraphs[0]._p)
        for child in list(cell._tc):
            if child.tag != qn("w:tcPr"):
                cell._tc.remove(child)
        for value in values or [""]:
            p = deepcopy(prototype)
            cell._tc.append(p)
            fill_paragraph(p, value, keep_next=is_heading)

    def insert_spacer():
        body.insert_element_before(deepcopy(spacer), "w:sectPr")

    def insert_table(template_index, title, content, add_spacer=True):
        element = deepcopy(prototypes[template_index])
        body.insert_element_before(element, "w:sectPr")
        table = Table(element, document)
        if template_index == 2 and not title:
            element.remove(table.rows[0]._tr)
            fill_cell(table.cell(0, 0), content)
        else:
            fill_cell(table.cell(0, 0), [title], is_heading=True)
            if len(table.rows) > 1:
                fill_cell(table.cell(1, 0), content)
        # Headers stay attached to the first plan line. Longer body rows may
        # flow across pages, so added wording never forces clipping.
        for row_index, row in enumerate(table.rows):
            is_header = bool(title) and row_index == 0
            trpr = row._tr.get_or_add_trPr()
            if not is_header:
                for cant_split in list(trpr.findall(qn("w:cantSplit"))):
                    trpr.remove(cant_split)
            for height in trpr.findall(qn("w:trHeight")):
                if height.get(qn("w:hRule")) == "exact":
                    height.set(qn("w:hRule"), "atLeast")
        if add_spacer:
            insert_spacer()

    for block in note_table_blocks(note_text, action_phrases=action_phrases):
        kind = block["kind"]
        if kind == "assessment":
            insert_table(0, block["heading"], block["lines"], add_spacer=False)
        elif kind == "indications" and block["heading"]:
            # Both care indications use the same blue heading and bordered
            # narrative row as ASSESSMENT in the user's updated template.
            previous = body[-2] if len(body) > 1 else None
            if previous is None or previous.tag != qn("w:p") or Paragraph(previous, document).text.strip():
                insert_spacer()
            insert_table(0, block["heading"], block["lines"])
        elif kind == "plan_heading":
            insert_table(1, block["heading"], [])
        elif kind in ("diagnosis", "plan_body"):
            insert_table(2, block["heading"], block["lines"])
        else:
            if block["heading"]:
                p = deepcopy(narrative)
                body.insert_element_before(p, "w:sectPr")
                fill_paragraph(p, block["heading"], bold=True, keep_next=True)
            for line in block["lines"]:
                p = deepcopy(narrative)
                body.insert_element_before(p, "w:sectPr")
                fill_paragraph(p, line)

    # Empty trailing space can push an otherwise finished note onto another page.
    while len(body) > 1 and body[-2].tag == qn("w:p") and not "".join(body[-2].itertext()).strip():
        body.remove(body[-2])
    output = BytesIO()
    document.save(output)
    return output.getvalue()


def build_table_preview(word_bytes):
    """Show the generated Word tables with literal, escaped clinical text."""
    from docx import Document
    from docx.oxml.ns import qn
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    document = Document(BytesIO(word_bytes))

    def paragraph_html(paragraph):
        if not paragraph.text:
            return '<p class="gap">&#160;</p>'
        parts = []
        for run in paragraph.runs:
            content = escape(run.text).replace("\n", "<br>")
            if run.bold:
                content = "<strong>" + content + "</strong>"
            if run.italic:
                content = "<em>" + content + "</em>"
            if run.underline:
                content = "<u>" + content + "</u>"
            parts.append(content)
        return "<p>" + ("".join(parts) or escape(paragraph.text)) + "</p>"

    blocks = []
    for element in document.element.body:
        if element.tag == qn("w:p"):
            blocks.append(paragraph_html(Paragraph(element, document)))
        elif element.tag == qn("w:tbl"):
            table = Table(element, document)
            rows = []
            for row in table.rows:
                cells = []
                for cell in row.cells:
                    shading = cell._tc.tcPr.find(qn("w:shd"))
                    fill = shading.get(qn("w:fill"), "FFFFFF") if shading is not None else "FFFFFF"
                    if not re.fullmatch(r"[0-9A-Fa-f]{6}", fill):
                        fill = "FFFFFF"
                    contents = "".join(paragraph_html(p) for p in cell.paragraphs)
                    cells.append(f'<td style="background-color:#{fill}">{contents}</td>')
                rows.append("<tr>" + "".join(cells) + "</tr>")
            blocks.append("<table>" + "".join(rows) + "</table>")
    return """<!doctype html><html lang="en"><head><meta charset="utf-8">
<style>
  body { margin: 0; padding: 12px; background: white; color: black;
    font-family: Aptos, Calibri, Arial, sans-serif; font-size: 12pt; line-height: 1.15; }
  table { border-collapse: collapse; width: 100%; table-layout: fixed; }
  td { border: 0.5pt solid black; padding: 2px 6px; overflow-wrap: break-word; }
  p { margin: 0; white-space: pre-wrap; }
  p.gap { height: 1em; }
</style></head><body>""" + "".join(blocks) + "</body></html>"


def word_filename(label):
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", label.strip()).strip("_")[:60]
    return f"u_{cleaned}.docx" if cleaned else "updated_note.docx"


def main():
    import streamlit as st

    st.set_page_config(page_title="Epic Plan Updater", layout="wide")
    st.title("Epic Plan Updater")
    st.caption(
        "Paste your assessment, clinical indications, and plan. "
        "Update the plan wording and download a Word note in your usual table layout."
    )

    defaults = {
        "note_input": "",
        "note_result": None,
        "note_error": "",
        "input_mode": FULL_NOTE,
        "source_choice": "Continue",
        "replacement_choice": "Will continue",
        "custom_source": "",
        "custom_replacement": "",
        "file_label": "",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    mode_column, label_column = st.columns((3, 2))
    with mode_column:
        input_mode = st.radio("Pasted content", (FULL_NOTE, PLAN_ONLY), key="input_mode", horizontal=True)
    with label_column:
        file_label = st.text_input("Room or file label (optional)", key="file_label", help="Used only for the Word filename.")
    note_input = st.text_area(
        "Paste from Epic here",
        key="note_input",
        height=310,
        help="Include the PLAN heading for a full note. Word output uses the table style from your template.",
    )
    left, right = st.columns(2)
    with left:
        source_choice = st.selectbox("Find phrase", PHRASES + (CUSTOM,), key="source_choice")
        source = st.text_input("Phrase to find", key="custom_source") if source_choice == CUSTOM else source_choice
    with right:
        replacement_choice = st.selectbox("Replace with", PHRASES + (CUSTOM,), key="replacement_choice")
        replacement = (
            st.text_input("Replacement phrase", key="custom_replacement")
            if replacement_choice == CUSTOM else replacement_choice
        )
    st.caption("Wording changes apply to plan instructions. Assessment and clinical indications keep their wording.")

    def clear_note():
        st.session_state["note_input"] = ""
        st.session_state["note_result"] = None
        st.session_state["note_error"] = ""
        st.session_state["file_label"] = ""

    current_input = (note_input, source, replacement, input_mode)
    action, clear = st.columns(2)
    with action:
        generate = st.button("Update note", type="primary")
    with clear:
        st.button("Clear note", on_click=clear_note)

    if generate:
        st.session_state["note_result"] = None
        st.session_state["note_error"] = ""
        try:
            result = update_note(note_input, source, replacement, input_mode)
            word_bytes = build_word_note(result.text, action_phrases=(source, replacement))
            st.session_state["note_result"] = {
                "text": result.text,
                "replacements": result.replacements,
                "input": current_input,
                "word_bytes": word_bytes,
                "table_preview": build_table_preview(word_bytes),
                "format_version": WORD_FORMAT_VERSION,
            }
        except ModuleNotFoundError as error:
            if error.name != "docx":
                raise
            st.session_state["note_error"] = (
                "Word export needs python-docx. Add python-docx to your requirements.txt, "
                "as in your original app, then reload."
            )
        except ValueError as error:
            st.session_state["note_error"] = str(error)

    if st.session_state["note_error"]:
        st.error(st.session_state["note_error"])

    saved = st.session_state["note_result"]
    if saved and ("word_bytes" not in saved or saved.get("format_version") != WORD_FORMAT_VERSION):
        # A running session can still hold a result from the previous app version.
        st.session_state["note_result"] = None
        saved = None
        st.info("Select Update note to prepare your Word download.")
    if saved and saved["input"] != current_input:
        st.info("The note or wording choices have changed. Select Update note to refresh the result.")
    elif saved:
        count = saved["replacements"]
        if count:
            st.success(f"Updated {count} plan {'phrase' if count == 1 else 'phrases'}.")
        else:
            st.info("No plan phrases needed replacement. Your Word note is ready.")
        st.download_button(
            "Download Word note",
            data=saved["word_bytes"],
            file_name=word_filename(file_label),
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key="word_download",
            type="primary",
        )
        st.subheader("Table preview")
        panel = saved["table_preview"]
        if hasattr(st, "iframe"):
            st.iframe(panel, height=600)
        else:
            # Preserve compatibility with existing apps on older Streamlit.
            import streamlit.components.v1 as components

            components.html(panel, height=600, scrolling=True)


if __name__ == "__main__":
    main()
