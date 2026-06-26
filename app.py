import json
import uuid
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import streamlit as st

# ── 상수 ─────────────────────────────────────────────
DATA_FILE = Path("todos.json")

CATEGORY_LABEL: Dict[str, str] = {"work": "업무", "personal": "개인", "study": "공부"}
CATEGORY_EMOJI: Dict[str, str] = {"work": "💼", "personal": "🏠", "study": "📚"}

FILTERS: List[str] = ["전체", "업무", "개인", "공부"]
LABEL_TO_KEY: Dict[str, str] = {"전체": "all", "업무": "work", "개인": "personal", "공부": "study"}
KEY_TO_LABEL: Dict[str, str] = {v: k for k, v in LABEL_TO_KEY.items()}

# ── 키워드 사전 ───────────────────────────────────────
KEYWORDS: Dict[str, List[str]] = {
    "work": [
        "회의", "미팅", "보고서", "기획", "업무", "프로젝트", "발표", "출장",
        "제안서", "계획서", "이메일", "메일", "전화", "클라이언트", "마감",
        "야근", "협업", "계약", "견적", "고객", "팀", "부서", "결재", "승인",
        "일정", "스케줄", "워크숍", "세미나", "인터뷰", "채용", "면접",
    ],
    "personal": [
        "운동", "헬스", "산책", "조깅", "친구", "가족", "부모", "형제",
        "쇼핑", "장보기", "마트", "여행", "나들이", "병원", "약속", "청소",
        "요리", "영화", "드라마", "게임", "취미", "휴식", "카페", "식당",
        "미용", "옷", "선물", "생일", "기념일", "데이트", "약", "건강",
    ],
    "study": [
        "공부", "강의", "책", "독서", "수업", "시험", "과제", "학교",
        "강좌", "독학", "연습", "복습", "예습", "논문", "자격증", "영어",
        "코딩", "프로그래밍", "개발", "수학", "과학", "역사", "어학",
        "토익", "토플", "자습", "인강", "유튜브", "강사", "튜터", "학원",
    ],
}

# ── 데이터 저장 / 불러오기 ────────────────────────────
def load_todos() -> List[dict]:
    if DATA_FILE.exists():
        try:
            return json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except Exception:
            return []
    return []

def save_todos(todos: List[dict]) -> None:
    DATA_FILE.write_text(json.dumps(todos, ensure_ascii=False, indent=2), encoding="utf-8")

# ── 키워드 자동 감지 ──────────────────────────────────
def detect_category(text: str) -> Tuple[str, List[str]]:
    """텍스트에서 카테고리와 매칭된 키워드 목록을 반환한다."""
    if not text.strip():
        return "work", []

    scores: Dict[str, List[str]] = {"work": [], "personal": [], "study": []}
    for cat, words in KEYWORDS.items():
        for word in words:
            if word in text:
                scores[cat].append(word)

    best = max(scores, key=lambda c: len(scores[c]))
    matched = scores[best]

    if not matched:
        return "work", []
    return best, matched

def on_text_change() -> None:
    text = st.session_state.get("new_todo_text", "")
    cat, matched = detect_category(text)
    st.session_state.auto_category = cat
    st.session_state.auto_matched = matched

# ── 진행률 계산 ───────────────────────────────────────
def get_progress(todos: List[dict], category: Optional[str] = None) -> Tuple[int, int, float]:
    items = todos if category is None else [t for t in todos if t["category"] == category]
    total = len(items)
    done = sum(1 for t in items if t["completed"])
    pct = done / total if total > 0 else 0.0
    return done, total, pct

# ── 세션 초기화 ───────────────────────────────────────
def init_session() -> None:
    defaults = {
        "todos": load_todos(),
        "filter": "전체",
        "editing_id": None,
        "edit_text": "",
        "auto_category": "work",
        "auto_matched": [],
        "input_key": 0,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# ── CRUD ─────────────────────────────────────────────
def add_todo(text: str, category_label: str) -> None:
    text = text.strip()
    if not text:
        return
    category = LABEL_TO_KEY.get(category_label, "work")
    st.session_state.todos.append({
        "id": str(uuid.uuid4()),
        "text": text,
        "category": category,
        "completed": False,
        "createdAt": int(time.time() * 1000),
    })
    save_todos(st.session_state.todos)
    st.session_state.input_key += 1
    st.session_state.auto_category = "work"
    st.session_state.auto_matched = []

def toggle_todo(todo_id: str) -> None:
    for t in st.session_state.todos:
        if t["id"] == todo_id:
            t["completed"] = not t["completed"]
            break
    save_todos(st.session_state.todos)

def delete_todo(todo_id: str) -> None:
    st.session_state.todos = [t for t in st.session_state.todos if t["id"] != todo_id]
    save_todos(st.session_state.todos)

def start_edit(todo_id: str, current_text: str) -> None:
    st.session_state.editing_id = todo_id
    st.session_state.edit_text = current_text

def commit_edit(todo_id: str) -> None:
    new_text = st.session_state.get("edit_input_{}".format(todo_id), "").strip()
    if new_text:
        for t in st.session_state.todos:
            if t["id"] == todo_id:
                t["text"] = new_text
                break
        save_todos(st.session_state.todos)
    st.session_state.editing_id = None
    st.session_state.edit_text = ""

def cancel_edit() -> None:
    st.session_state.editing_id = None
    st.session_state.edit_text = ""

def clear_all() -> None:
    st.session_state.todos = []
    save_todos(st.session_state.todos)

# ── CSS ──────────────────────────────────────────────
def inject_css() -> None:
    st.markdown("""
    <style>
    #MainMenu, footer, header { visibility: hidden; }
    .block-container { padding-top: 2rem; max-width: 720px; }

    .app-title { font-size: 28px; font-weight: 800; letter-spacing: -0.5px; margin-bottom: 0; }
    .app-title span { color: #4F86F7; }

    .progress-card {
        background: #fff; border-radius: 12px;
        padding: 20px; margin-bottom: 16px;
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
    .cat-bar-fill { height: 100%; border-radius: 99px; }

    .badge {
        display: inline-block; font-size: 11px; font-weight: 700;
        padding: 2px 10px; border-radius: 99px; color: #fff;
    }
    .badge-work     { background: #4F86F7; }
    .badge-personal { background: #F97B6B; }
    .badge-study    { background: #6BCB77; }

    .detect-box {
        display: flex; align-items: center; gap: 8px;
        background: #F0F7FF; border: 1px solid #BFDBFE;
        border-radius: 8px; padding: 8px 12px;
        font-size: 13px; margin-bottom: 8px;
    }
    .detect-box.personal { background: #FFF5F4; border-color: #FECACA; }
    .detect-box.study    { background: #F0FDF4; border-color: #BBF7D0; }
    .detect-label { font-weight: 700; }
    .detect-keywords span {
        display: inline-block; background: #DBEAFE;
        color: #1D4ED8; font-size: 11px; font-weight: 600;
        padding: 1px 7px; border-radius: 99px; margin-right: 4px;
    }
    .detect-keywords.personal span { background: #FFE4E1; color: #B91C1C; }
    .detect-keywords.study    span { background: #DCFCE7; color: #166534; }

    .todo-card {
        background: #fff; border-radius: 12px;
        padding: 14px 16px; margin-bottom: 8px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
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

# ── 자동 감지 힌트 UI ─────────────────────────────────
def render_detect_hint() -> None:
    cat = st.session_state.auto_category
    matched = st.session_state.auto_matched
    if not matched:
        return

    color_class = {"work": "", "personal": "personal", "study": "study"}.get(cat, "")
    label = "{} 자동 감지: {}".format(CATEGORY_EMOJI[cat], CATEGORY_LABEL[cat])
    keywords_html = "".join("<span>{}</span>".format(w) for w in matched)

    st.markdown("""
    <div class="detect-box {color_class}">
      <span class="detect-label">{label}</span>
      <span class="detect-keywords {color_class}">{keywords_html}</span>
    </div>
    """.format(color_class=color_class, label=label, keywords_html=keywords_html),
        unsafe_allow_html=True,
    )

# ── 진행률 카드 ───────────────────────────────────────
def render_progress(todos: List[dict]) -> None:
    done_all, total_all, pct_all = get_progress(todos)
    cats = [
        ("work",     "업무", "#4F86F7"),
        ("personal", "개인", "#F97B6B"),
        ("study",    "공부", "#6BCB77"),
    ]
    cat_stats = {c: get_progress(todos, c) for c, _, _ in cats}

    cat_bars_html = "".join(
        """<div class="cat-item">
              <div class="cat-name">{label}
                <span class="cat-count">{done}/{total}</span>
              </div>
              <div class="cat-bar-bg">
                <div class="cat-bar-fill" style="width:{pct}%;background:{color};"></div>
              </div>
            </div>""".format(
            label=label,
            done=cat_stats[key][0],
            total=cat_stats[key][1],
            pct=int(cat_stats[key][2] * 100),
            color=color,
        )
        for key, label, color in cats
    )

    st.markdown("""
    <div class="progress-card">
      <div class="progress-total-label">전체 진행률</div>
      <div class="progress-total-pct">{pct}%</div>
      <div style="background:#E5E7EB;border-radius:99px;height:8px;overflow:hidden;margin-bottom:20px;">
        <div style="width:{pct}%;height:100%;border-radius:99px;background:#4F86F7;transition:width 0.3s;"></div>
      </div>
      <div class="cat-row">{cat_bars}</div>
    </div>
    """.format(pct=int(pct_all * 100), cat_bars=cat_bars_html),
        unsafe_allow_html=True,
    )

# ── 할 일 목록 ────────────────────────────────────────
def render_todos(todos: List[dict]) -> None:
    filter_val = st.session_state.filter
    cat_key = LABEL_TO_KEY[filter_val]
    visible = todos if cat_key == "all" else [t for t in todos if t["category"] == cat_key]

    done_all, total_all, _ = get_progress(todos)
    if total_all > 0 and done_all == total_all:
        st.markdown('<div class="congrats">🎉 모든 할 일을 완료했어요!</div>', unsafe_allow_html=True)

    if not visible:
        st.markdown(
            "<p style='color:#9CA3AF;text-align:center;padding:24px 0;'>할 일이 없습니다.</p>",
            unsafe_allow_html=True,
        )
        return

    for todo in visible:
        cat = todo["category"]
        badge = '<span class="badge badge-{cat}">{label}</span>'.format(
            cat=cat, label=CATEGORY_LABEL[cat]
        )
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
                        key="edit_input_{}".format(todo["id"]),
                        label_visibility="collapsed",
                    )
                with col_save:
                    if st.button("저장", key="save_{}".format(todo["id"])):
                        commit_edit(todo["id"])
                        st.rerun()
                with col_cancel:
                    if st.button("취소", key="cancel_{}".format(todo["id"])):
                        cancel_edit()
                        st.rerun()
            else:
                col_check, col_badge, col_text, col_edit, col_del = st.columns([0.5, 1.2, 5, 0.8, 0.8])
                with col_check:
                    st.checkbox(
                        "",
                        value=todo["completed"],
                        key="check_{}".format(todo["id"]),
                        on_change=toggle_todo,
                        args=(todo["id"],),
                    )
                with col_badge:
                    st.markdown(badge, unsafe_allow_html=True)
                with col_text:
                    st.markdown(
                        '<p class="{cls}" style="margin:6px 0;">{text}</p>'.format(
                            cls=text_class, text=todo["text"]
                        ),
                        unsafe_allow_html=True,
                    )
                with col_edit:
                    if st.button("✏", key="edit_{}".format(todo["id"])):
                        start_edit(todo["id"], todo["text"])
                        st.rerun()
                with col_del:
                    if st.button("✕", key="del_{}".format(todo["id"])):
                        delete_todo(todo["id"])
                        st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

# ── 메인 ─────────────────────────────────────────────
def main() -> None:
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

    render_progress(todos)

    # 필터 탭
    st.session_state.filter = st.radio(
        "필터", FILTERS,
        index=FILTERS.index(st.session_state.filter),
        horizontal=True,
        label_visibility="collapsed",
    )

    st.markdown("---")

    # 입력 영역 — input_key 카운터로 추가 후 입력창 초기화
    input_key = "new_todo_text_{}".format(st.session_state.input_key)
    cat_key   = "cat_select_{}".format(st.session_state.input_key)

    col_text, col_cat, col_add = st.columns([4, 1.5, 1])
    with col_text:
        current_text = st.text_input(
            "할 일",
            placeholder="할 일을 입력하세요  (키워드 자동 감지)",
            key=input_key,
            on_change=on_text_change,
            label_visibility="collapsed",
        )
        st.session_state["new_todo_text"] = current_text

    auto_label = KEY_TO_LABEL.get(st.session_state.auto_category, "업무")
    cat_options = ["업무", "개인", "공부"]
    default_idx = cat_options.index(auto_label) if auto_label in cat_options else 0

    with col_cat:
        input_category = st.selectbox(
            "카테고리", cat_options,
            index=default_idx,
            key=cat_key,
            label_visibility="collapsed",
        )
    with col_add:
        if st.button("+ 추가", use_container_width=True, key="btn_add"):
            add_todo(current_text, input_category)
            st.rerun()

    # 자동 감지 힌트
    render_detect_hint()

    # 할 일 목록
    render_todos(st.session_state.todos)

if __name__ == "__main__":
    main()
