import streamlit as st
import json
import re
import random

#----------------------------------------------------------
# Page setup & Custom CSS
#----------------------------------------------------------
st.set_page_config(page_title="Prompt Template Lookup", layout="wide")
st.markdown("""
<style>
/* Sidebar width */
.css-1d391kg .css-18e3th9 { max-width: 300px; }
/* Button styling */
div.stButton > button {
    border-radius: 8px;
    padding: 0.6em 1em;
    font-size: 16px;
    width: 100%;
}
#clear-btn button { background-color: #FF6B6B !important; color: white; }
body { background-color: #0E1117; color: #E0E0E0; }
</style>
""", unsafe_allow_html=True)

#----------------------------------------------------------
# Load templates
def load_templates():
    with open("prompt_templates.json", "r", encoding="utf-8") as f:
        return json.load(f)
templates = st.cache_data(load_templates)()

#----------------------------------------------------------
# Sidebar: Search & Language
#----------------------------------------------------------
st.sidebar.markdown("## 🔍 Search & Navigate", unsafe_allow_html=True)
search_query = st.sidebar.text_input("关键词 / Search", placeholder="例如：email 或 面试")
language = st.sidebar.radio("语言 / Language", ["中文", "English"])
lang = 'zh' if language == '中文' else 'en'

# Collect search matches (search in both languages regardless of UI lang)
search_matches = []
if search_query:
    q = search_query.strip().lower()
    for big, subs in templates.items():
        for sub_key, obj in subs.items():
            # Gather all searchable text
            texts = [big, sub_key,
                     obj['template_name']['zh'], obj['template_name']['en'],
                     obj['content']['zh'], obj['content']['en']]
            if any(q in t.lower() for t in texts):
                # Display label in current UI language
                display = obj['template_name'][lang]
                search_matches.append((big, sub_key, display))
    if search_matches:
        st.sidebar.markdown("### 🔎 搜索结果 / Search Results")
        for big, sub_key, display in search_matches:
            if st.sidebar.button(display, key=f"search_{big}_{sub_key}"):
                st.session_state['search_choice'] = (big, sub_key)
    else:
        st.sidebar.warning("未找到匹配模板 / No matches found")

st.sidebar.markdown("---")

#----------------------------------------------------------
# Sidebar: Full Catalog
#----------------------------------------------------------
st.sidebar.markdown("## 📂 目录 / Catalog", unsafe_allow_html=True)
# Determine defaults from search or reset
if 'search_choice' in st.session_state:
    default_big, default_sub = st.session_state['search_choice']
else:
    default_big, default_sub = None, None

big_list = list(templates.keys())
big_idx = big_list.index(default_big) if default_big in big_list else 0
select_big = st.sidebar.selectbox("场景 / Field", big_list, index=big_idx)

sub_list = list(templates[select_big].keys())
sub_idx = sub_list.index(default_sub) if default_sub in sub_list else 0
select_sub = st.sidebar.selectbox("模板 / Template", sub_list, index=sub_idx)

# Sync choice
st.session_state['search_choice'] = (select_big, select_sub)

#----------------------------------------------------------
# Main: Title & Template Preview
#----------------------------------------------------------
st.title("🧠 Prompt Template Lookup Tool")
#st.markdown("支持搜索、目录浏览、模板预览与实时填充。", unsafe_allow_html=True)

# Load selected template
tpl_obj = templates[select_big][select_sub]
tpl_name = tpl_obj['template_name'][lang]
tpl_content = tpl_obj['content'][lang]

st.subheader(f"📋 Template Preview / {tpl_name}")
st.code(tpl_content, language='text')

#----------------------------------------------------------
# Main: Fill Inputs
#----------------------------------------------------------
# Extract placeholders
fields = re.findall(r"\{(.+?)\}", tpl_content)
# Initialize input state on template change
tpl_key = f"{select_big}__{select_sub}"
if st.session_state.get('current_tpl') != tpl_key:
    st.session_state['current_tpl'] = tpl_key
    st.session_state['inputs'] = {f: '' for f in fields}
    st.session_state['key_prefix'] = str(random.random())

st.markdown("---")
st.subheader("填写内容 / Fill Inputs")
# Two-column layout
cols = st.columns(2)
for idx, field in enumerate(fields):
    col = cols[idx % 2]
    val = col.text_area(
        f"{field.replace('_', ' ').capitalize()}",
        value=st.session_state['inputs'][field],
        height=80,
        key=st.session_state['key_prefix'] + field
    )
    st.session_state['inputs'][field] = val

# Clear inputs button below
if st.button("🔄 清空填写 / Clear Inputs", key='clear-btn'):
    st.session_state['inputs'] = {f: '' for f in fields}
    st.session_state['key_prefix'] = str(random.random())

#----------------------------------------------------------
# Main: Build & Preview Filled Prompt
#----------------------------------------------------------
filled_lines = []
for line in tpl_content.splitlines():
    phs = re.findall(r"\{(.+?)\}", line)
    # Skip lines with unfilled placeholders
    if any(not st.session_state['inputs'].get(ph, '').strip() for ph in phs):
        continue
    tmp = line
    for ph, rv in st.session_state['inputs'].items():
        tmp = tmp.replace(f"{{{ph}}}", rv.strip() or f"<{ph}>")
    filled_lines.append(tmp)
filled_prompt = "\n".join(filled_lines)

st.markdown("---")
st.subheader("👀 实时预览 / Prompt Preview")
st.code(filled_prompt, language='text')

# Download button in sidebar
st.sidebar.download_button(
    "Download",
    filled_prompt,
    file_name="prompt.txt",
    mime="text/plain"
)
