import json
import uuid
import time
from pathlib import Path
import streamlit as st

# ── 상수 ─────────────────────────────────────────────
DATA_FILE = Path("todos.json")
CATEGORY_LABEL = {"work": "업무", "personal": "개인", "study": "공부"}
CATEGORY_COLOR = {"work": "#4F86F7", "personal": "#F97B6B", "study": "#6BCB77"}
FILTERS = ["전체", "업무", "개인", "공부"]
FILTER_KEY = {"전체": "all", "업무": "work", "개인": "personal", "공부": "study"}

# ── 데이터 저장 / 불러오기 ────────────────────────────
def load_todos():
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []

def save_todos(todos):
    DATA_FILE.write_text(json.dumps(todos, ensure_ascii=False, indent=2), encoding="utf-8")

# ── 진행률 계산 ───────────────────────────────────────
def get_progress(todos, category=None):
    items = todos if category is None else [t for t in todos if t["category"] == category]
    total = len(items)
    done = sum(1 for t in items if t["completed"])
    pct = done / total if total > 0 else 0
    return done, total, pct

# ── 세션 초기화 ───────────────────────────────────────
def init_session():
    if "todos" not in st.session_state:
        st.session_state.todos = load_todos()
    if "filter" not in st.session_state:
        st.session_state.filter = "전체"
    if "editing_id" not in st.session_state:
        st.session_state.editing_id = None
    if "edit_text" not in st.session_state:
        st.session_state.edit_text = ""

# ── 액션 핸들러 ──────────────────────────────────────
def add_todo():
    text = st.session_state.get("input_text", "").strip()
    category = FILTER_KEY.get(st.session_state.get("input_category", "업무"), "work")
    if not text:
        return
    st.session_state.todos.append({
        "id": str(uuid.uuid4()),
        "text": text,
        "category": category,
        "completed": False,
        "createdAt": int(time.time() * 1000),
    })
    save_todos(st.session_state.todos)
    st.session_state.input_text = ""

def toggle_todo(todo_id):
    for t in st.session_state.todos:
        if t["id"] == todo_id:
            t["completed"] = not t["completed"]
            break
    save_todos(st.session_state.todos)

def delete_todo(todo_id):
    st.session_state.todos = [t for t in st.session_state.todos if t["id"] != todo_id]
    save_todos(st.session_state.todos)

def start_edit(todo_id, current_text):
    st.session_state.editing_id = todo_id
    st.session_state.edit_text = current_text

def commit_edit(todo_id):
    new_text = st.session_state.get(f"edit_input_{todo_id}", "").strip()
    if new_text:
        for t in st.session_state.todos:
            if t["id"] == todo_id:
                t["text"] = new_text
                break
        save_todos(st.session_state.todos)
    st.session_state.editing_id = None
    st.session_state.edit_text = ""

def cancel_edit():
    st.session_state.editing_id = None
    st.session_state.edit_text = ""

def clear_all():
    st.session_state.todos = []
    save_todos(st.session_state.todos)

# ── CSS ──────────────────────────────────────────────
def inject_css():
    st.markdown("""
    <style>
    :root {
        --color-work:     #4F86F7;
        --color-personal: #F97B6B;
        --color-study:    #6BCB77;
    }
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 2rem; max-width: 700px; }

    .app-title { font-size: 28px; font-weight: 800; letter-spacing: -0.5px; margin-bottom: 0; }
    .app-title span { color: #4F86F7; }

    .progress-card {
        background: #fff;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 16px;
        box-shadow: 0 1px 4px rgba(0,0,0,0.06);
    }
    .progress-total-label {
        font-size: 12px; font-weight: 600; color: #9CA3AF;
        text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 4px;
    }
    .progress-total-pct { font-size: 30px; font-weight: 800; color: #1A1A2E; margin-bottom: 8px; }

    .cat-row { display: flex; gap: 16px; margin-top: 8px; }
    .cat-item { flex: 1; }
    .cat-name { font-size: 12px; font-weight: 600; margin-bottom: 4px; color: #1A1A2E; }
    .cat-count { font-size: 11px; color: #9CA3AF; float: right; }
    .cat-bar-bg { background: #E5E7EB; border-radius: 99px; height: 6px; overflow: hidden; }
    .cat-bar-fill { height: 100%; border-radius: 99px; transition: width 0.3s; }

    .badge {
        display: inline-block;
        font-size: 11px; font-weight: 700;
        padding: 2px 10px; border-radius: 99px; color: #fff;
    }
    .badge-work     { background: #4F86F7; }
    .badge-personal { background: #F97B6B; }
    .badge-study    { background: #6BCB77; }

    .todo-card {
        background: #fff; border-radius: 12px;
        padding: 14px 16px; margin-bottom: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        transition: box-shadow 0.15s;
    }
    .todo-card:hover { box-shadow: 0 4px 12px rgba(0,0,0,0.09); }
    .todo-text-done { text-decoration: line-through; color: #9CA3AF; }

    .congrats {
        text-align: center; padding: 24px; font-size: 17px; font-weight: 700;
        color: #6BCB77; background: #fff; border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05); margin-bottom: 8px;
    }

    div[data-testid="stHorizontalBlock"] > div { padding: 0 4px; }
    </style>
    """, unsafe_allow_html=True)

# ── 진행률 카드 렌더 ──────────────────────────────────
def render_progress(todos):
    done_all, total_all, pct_all = get_progress(todos)

    cats = [
        ("work",     "업무", "#4F86F7"),
        ("personal", "개인", "#F97B6B"),
        ("study",    "공부", "#6BCB77"),
    ]
    cat_stats = {c: get_progress(todos, c) for c, _, _ in cats}

    cat_bars_html = "".join(
        f"""<div class="cat-item">
              <div class="cat-name">{label}<span class="cat-count">{cat_stats[key][0]}/{cat_stats[key][1]}</span></div>
              <div class="cat-bar-bg">
                <div class="cat-bar-fill" style="width:{cat_stats[key][2]*100:.0f}%;background:{color};"></div>
              </div>
            </div>"""
        for key, label, color in cats
    )

    st.markdown(f"""
    <div class="progress-card">
      <div class="progress-total-label">전체 진행률</div>
      <div class="progress-total-pct">{pct_all*100:.0f}%</div>
      <div style="background:#E5E7EB;border-radius:99px;height:8px;overflow:hidden;margin-bottom:20px;">
        <div style="width:{pct_all*100:.0f}%;height:100%;border-radius:99px;background:#4F86F7;transition:width 0.3s;"></div>
      </div>
      <div class="cat-row">{cat_bars_html}</div>
    </div>
    """, unsafe_allow_html=True)

# ── 할 일 목록 렌더 ───────────────────────────────────
def render_todos(todos):
    filter_val = st.session_state.filter
    cat_key = FILTER_KEY[filter_val]
    visible = todos if cat_key == "all" else [t for t in todos if t["category"] == cat_key]

    done_all, total_all, _ = get_progress(todos)
    if total_all > 0 and done_all == total_all:
        st.markdown('<div class="congrats">🎉 모든 할 일을 완료했어요!</div>', unsafe_allow_html=True)

    if not visible:
        st.markdown("<p style='color:#9CA3AF;text-align:center;padding:24px 0;'>할 일이 없습니다.</p>",
                    unsafe_allow_html=True)
        return

    for todo in visible:
        badge = f'<span class="badge badge-{todo["category"]}">{CATEGORY_LABEL[todo["category"]]}</span>'
        is_editing = st.session_state.editing_id == todo["id"]
        text_class = "todo-text-done" if todo["completed"] else ""

        with st.container():
            st.markdown('<div class="todo-card">', unsafe_allow_html=True)

            if is_editing:
                col_input, col_save, col_cancel = st.columns([6, 1, 1])
                with col_input:
                    st.text_input(
                        "수정",
                        value=st.session_state.edit_text,
                        key=f"edit_input_{todo['id']}",
                        label_visibility="collapsed",
                    )
                with col_save:
                    if st.button("저장", key=f"save_{todo['id']}"):
                        commit_edit(todo["id"])
                        st.rerun()
                with col_cancel:
                    if st.button("취소", key=f"cancel_{todo['id']}"):
                        cancel_edit()
                        st.rerun()
            else:
                col_check, col_badge, col_text, col_edit, col_del = st.columns([0.5, 1.2, 5, 0.8, 0.8])
                with col_check:
                    checked = st.checkbox(
                        "", value=todo["completed"],
                        key=f"check_{todo['id']}",
                        on_change=toggle_todo, args=(todo["id"],),
                    )
                with col_badge:
                    st.markdown(badge, unsafe_allow_html=True)
                with col_text:
                    st.markdown(
                        f'<p class="{text_class}" style="margin:6px 0;">{todo["text"]}</p>',
                        unsafe_allow_html=True,
                    )
                with col_edit:
                    if st.button("✏", key=f"edit_{todo['id']}"):
                        start_edit(todo["id"], todo["text"])
                        st.rerun()
                with col_del:
                    if st.button("✕", key=f"del_{todo['id']}"):
                        delete_todo(todo["id"])
                        st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

# ── 메인 ─────────────────────────────────────────────
def main():
    st.set_page_config(page_title="To do Flow", page_icon="✅", layout="centered")
    inject_css()
    init_session()

    todos = st.session_state.todos

    # 헤더
    col_title, col_reset = st.columns([5, 1])
    with col_title:
        st.markdown('<p class="app-title">To do <span>Flow</span></p>', unsafe_allow_html=True)
    with col_reset:
        if st.button("초기화", key="btn_reset"):
            clear_all()
            st.rerun()

    # 진행률 카드
    render_progress(todos)

    # 필터 탭
    st.session_state.filter = st.radio(
        "필터",
        FILTERS,
        index=FILTERS.index(st.session_state.filter),
        horizontal=True,
        label_visibility="collapsed",
    )

    # 입력 영역
    col_text, col_cat, col_add = st.columns([4, 1.5, 1])
    with col_text:
        st.text_input(
            "할 일",
            placeholder="할 일을 입력하세요",
            key="input_text",
            label_visibility="collapsed",
        )
    with col_cat:
        st.selectbox(
            "카테고리",
            ["업무", "개인", "공부"],
            key="input_category",
            label_visibility="collapsed",
        )
    with col_add:
        if st.button("+ 추가", use_container_width=True):
            add_todo()
            st.rerun()

    st.markdown("---")

    # 할 일 목록
    render_todos(st.session_state.todos)

if __name__ == "__main__":
    main()
