# src/components/summary_display.py
import streamlit as st
from streamlit.components.v1 import html
import re
from src.components.icons import load_icon_base64

copy_icon_b64 = load_icon_base64("copy_icon.png")
copied_icon_b64 = load_icon_base64("copied_icon.png")

def display_summary(content: str):
    sections = re.split(r'\n## ', content)
    formatted_content = ""
    for section in sections:
        if not section.strip():
            continue
        if '\n' in section:
            title, body = section.split('\n', 1)
        else:
            title, body = section, ""
        body = re.sub(r'^- (.*?)$', r'- \1', body, flags=re.MULTILINE)
        formatted_content += f"## {title}\n{body}\n\n"
    st.markdown(formatted_content, unsafe_allow_html=True)

    unique_key = f"summary-{abs(hash(content))}"
    safe_content = content.replace("`", "\\`").replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')
    html_code = f"""
    <div style="text-align:right; margin-top:16px">
        <button id="copy-summary-btn" style="border:none; background:none; cursor:pointer;">
            <img id="copy-summary-icon" src="data:image/png;base64,{copy_icon_b64}" width="22" height="22"/> Copy Summary
        </button>
    </div>
    <script>
    document.getElementById("copy-summary-btn").addEventListener('click', function() {{
        const content = "{safe_content}";
        navigator.clipboard.writeText(content).then(function() {{
            const icon = document.getElementById("copy-summary-icon");
            icon.src = "data:image/png;base64,{copied_icon_b64}";
            setTimeout(function() {{
                icon.src = "data:image/png;base64,{copy_icon_b64}";
            }}, 1200);
        }});
    }});
    </script>
    """
    html(html_code, height=60)
