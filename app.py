"""Update Epic plan wording and return a note that can be copied as plain text.

Run with: streamlit run app.py
Only Streamlit is required. Note text stays in the current Streamlit session.
"""

from dataclasses import dataclass
from html import escape
import re


PHRASES = ("Continue", "Will continue", "We will continue", "We shall continue")
CUSTOM = "Custom phrase"
FULL_NOTE = "Assessment, indications, and plan"
PLAN_ONLY = "Plan only"

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


def build_copy_panel(note_text):
    """Render literal, selectable note text with a clipboard button and fallback."""
    return """<!doctype html>
<html lang="en">
<head><meta charset="utf-8"><style>
  :root { color-scheme: light dark; }
  body { margin: 0; font-family: system-ui, sans-serif; }
  label { display: block; font-size: 14px; margin-bottom: 8px; }
  textarea { box-sizing: border-box; width: 100%; height: 420px;
    padding: 14px; border: 1px solid #888; border-radius: 8px;
    font: 15px/1.5 system-ui, sans-serif; resize: vertical; }
  button { margin-top: 12px; padding: 9px 18px; border: 1px solid #888;
    border-radius: 7px; font: 600 14px system-ui, sans-serif; cursor: pointer; }
  button:focus-visible, textarea:focus-visible { outline: 3px solid #597dbd; }
  #copy-status { display: inline-block; margin: 10px; font-size: 14px; }
</style></head>
<body>
<label for="epic-note">Updated note</label>
<textarea id="epic-note" readonly spellcheck="false">""" + escape(note_text) + """</textarea>
<button type="button" id="copy-note">Copy note</button>
<span id="copy-status" role="status" aria-live="polite"></span>
<script>
  const note = document.getElementById('epic-note');
  const status = document.getElementById('copy-status');
  document.getElementById('copy-note').addEventListener('click', async () => {
    try {
      if (!navigator.clipboard || !window.isSecureContext) throw new Error('fallback');
      await navigator.clipboard.writeText(note.value);
      status.textContent = 'Copied. Paste into Epic.';
    } catch (error) {
      note.focus();
      note.select();
      note.setSelectionRange(0, note.value.length);
      let copied = false;
      try { copied = document.execCommand('copy'); } catch (copyError) {}
      status.textContent = copied ? 'Copied. Paste into Epic.' :
        'Text selected. Press Ctrl+C or Command+C, then paste into Epic.';
    }
  });
</script>
</body></html>"""


def main():
    import streamlit as st

    st.set_page_config(page_title="Epic Plan Updater", layout="wide")
    st.title("Epic Plan Updater")
    st.caption(
        "Paste your assessment, clinical indications, and plan. "
        "Update the plan wording, then copy the result into Epic."
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
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    input_mode = st.radio("Pasted content", (FULL_NOTE, PLAN_ONLY), key="input_mode", horizontal=True)
    note_input = st.text_area(
        "Paste from Epic here",
        key="note_input",
        height=310,
        help="Copied table text is accepted. Include the PLAN heading when pasting a full note.",
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
            st.session_state["note_result"] = {
                "text": result.text,
                "replacements": result.replacements,
                "input": current_input,
            }
        except ValueError as error:
            st.session_state["note_error"] = str(error)

    if st.session_state["note_error"]:
        st.error(st.session_state["note_error"])

    saved = st.session_state["note_result"]
    if saved and saved["input"] != current_input:
        st.info("The note or wording choices have changed. Select Update note to refresh the result.")
    elif saved:
        count = saved["replacements"]
        if count:
            st.success(f"Updated {count} plan {'phrase' if count == 1 else 'phrases'}.")
        else:
            st.info("No plan phrases needed replacement. The retained note is below.")
        panel = build_copy_panel(saved["text"])
        if hasattr(st, "iframe"):
            st.iframe(panel, height=530)
        else:
            # Preserve compatibility with existing apps on older Streamlit.
            import streamlit.components.v1 as components

            components.html(panel, height=530, scrolling=True)


if __name__ == "__main__":
    main()
