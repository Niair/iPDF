# src/components/message_renderer.py
import streamlit as st
from streamlit.components.v1 import html
from src.components.icons import load_icon_base64

copy_icon_b64 = load_icon_base64("copy_icon.png")
copied_icon_b64 = load_icon_base64("copied_icon.png")

def render_message_with_copy(text: str, role: str, idx: int):
    if role == "assistant":
        st.chat_message(role).markdown(text)
    else:
        st.chat_message(role).write(text)

    safe_text = text.replace("`", "\\`").replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')

    html_code = f"""
    <div style="margin-top: -8px; margin-bottom: 12px; display:flex; align-items:center;">
      <button onclick="copyText{idx}()" style="border:none; background:none; cursor:pointer; padding:0;">
        <img id="copy-icon-{idx}" src="data:image/png;base64,{copy_icon_b64}" width="18" height="18"/>
      </button>
    </div>
    <script>
    function copyText{idx}() {{
        const text = "{safe_text}";
        navigator.clipboard.writeText(text).then(function() {{
            const icon = document.getElementById("copy-icon-{idx}");
            icon.src = "data:image/png;base64,{copied_icon_b64}";
            setTimeout(function() {{
                icon.src = "data:image/png;base64,{copy_icon_b64}";
            }}, 1000);
        }});
    }}
    </script>
    """
    html(html_code, height=32)
