"""
Copy Button Component
Reusable copy-to-clipboard functionality
"""
import streamlit as st


def render_copy_button(content: str, button_text: str = "📋 Copy", key: str = None):
    """
    Render a copy button
    
    Args:
        content: Content to copy
        button_text: Button label
        key: Unique key for button
    """
    if st.button(button_text, key=key):
        # Show content in a code block for easy copying
        st.code(content, language=None)
        st.success("✅ Content ready to copy!")


def copy_to_clipboard_js(content: str, button_id: str):
    """
    Generate JavaScript for copy to clipboard (alternative method)
    
    Args:
        content: Content to copy
        button_id: Button ID
        
    Returns:
        HTML/JS string
    """
    # Escape content for JavaScript
    escaped_content = content.replace("'", "\\'").replace("\n", "\\n")
    
    html = f"""
    <button id="{button_id}" onclick="copyToClipboard()">📋 Copy</button>
    <script>
    function copyToClipboard() {{
        const content = '{escaped_content}';
        navigator.clipboard.writeText(content).then(function() {{
            document.getElementById('{button_id}').innerText = '✅ Copied!';
            setTimeout(function() {{
                document.getElementById('{button_id}').innerText = '📋 Copy';
            }}, 2000);
        }});
    }}
    </script>
    """
    
    return html
