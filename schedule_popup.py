from __future__ import annotations

from datetime import date, datetime

import streamlit as st

from now_time import load_schedule, save_schedule, sort_by_priority


def priority_badge(priority: int) -> str:
    """優先度に応じてスタイル付きバッジ HTML を返す。"""
    colors = {
        3: "#ff4b4b",  # 最重要
        2: "#ffb347",
        1: "#3cb371",
    }
    labels = {
        3: "High",
        2: "Medium",
        1: "Low",
    }
    color = colors.get(priority, "#3cb371")
    label = labels.get(priority, "Low")
    return f"""
    <span style="
        background: {color};
        color: white;
        padding: 2px 10px;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 600;
        letter-spacing: 0.03em;
    ">{label}</span>
    """


def apply_global_style() -> None:
    """全体のスタイルを少しゴージャスにする CSS を適用。"""
    st.markdown(
        """
        <style>
        .main {
            background: radial-gradient(circle at top left, #1f2933 0, #111827 45%, #020617 100%);
            color: #e5e7eb;
        }
        section[data-testid="stSidebar"] {
            background: linear-gradient(180deg, #020617 0%, #0b1120 50%, #020617 100%);
            border-right: 1px solid rgba(148, 163, 184, 0.3);
        }
        .todo-card {
            background: linear-gradient(135deg, rgba(15,23,42,0.9), rgba(30,64,175,0.7));
            border-radius: 18px;
            padding: 16px 18px;
            border: 1px solid rgba(148, 163, 184, 0.5);
            box-shadow: 0 18px 45px rgba(15, 23, 42, 0.9);
            backdrop-filter: blur(18px);
            margin-bottom: 14px;
        }
        .todo-title {
            font-size: 1rem;
            font-weight: 600;
            letter-spacing: 0.02em;
            color: #e5e7eb;
        }
        .todo-meta {
            font-size: 0.8rem;
            color: #9ca3af;
        }
        .glass-panel {
            background: linear-gradient(135deg, rgba(15,23,42,0.85), rgba(6,78,59,0.7));
            border-radius: 18px;
            padding: 18px 20px;
            border: 1px solid rgba(45, 212, 191, 0.4);
            box-shadow: 0 18px 45px rgba(15, 23, 42, 0.9);
            backdrop-filter: blur(18px);
        }
        .metric-label {
            font-size: 0.75rem;
            text-transform: uppercase;
            letter-spacing: 0.18em;
            color: #9ca3af;
        }
        .metric-value {
            font-size: 1.4rem;
            font-weight: 700;
            color: #e5e7eb;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(today_str: str, items_count: int, high_count: int) -> None:
    """サイドバーに日付やサマリを表示。"""
    with st.sidebar:
        st.markdown("### 今日")
        st.markdown(f"**{today_str}**")

        st.markdown("---")
        st.markdown("### サマリ")
        col1, col2 = st.columns(2)
        with col1:
            st.markdown('<div class="metric-label">Total</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="metric-value">{items_count}</div>',
                unsafe_allow_html=True,
            )
        with col2:
            st.markdown('<div class="metric-label">High</div>', unsafe_allow_html=True)
            st.markdown(
                f'<div class="metric-value">{high_count}</div>',
                unsafe_allow_html=True,
            )

        st.markdown("---")
        st.caption("この画面は `schedule.json` をリアルタイムに読み書きします。")


def render_todo_list(items: list[dict]) -> None:
    """ToDo一覧をカードスタイルで表示。"""
    if not items:
        st.info("まだ予定が登録されていません。右上のフォームから追加できます。")
        return

    for item in items:
        title = str(item.get("title", ""))
        priority = int(item.get("priority", 1))
        created_at = str(item.get("created_at", ""))
        created_dt = created_at
        if "T" in created_at:
            created_dt = created_at.replace("T", " ")

        badge = priority_badge(priority)

        st.markdown(
            f"""
            <div class="todo-card">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                    <div class="todo-title">{title}</div>
                    <div>{badge}</div>
                </div>
                <div class="todo-meta">
                    登録日時: {created_dt}
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_add_form(items: list[dict]) -> list[dict]:
    """予定追加フォームを表示して保存まで行う。"""
    with st.form("add_todo_form"):
        st.subheader("予定を追加")
        title = st.text_input("予定", placeholder="例: 資料作成, ミーティング準備 など")
        priority = st.select_slider(
            "重要度 (右に行くほど重要)",
            options=[1, 2, 3],
            value=2,
            format_func=lambda x: {1: "Low (1)", 2: "Medium (2)", 3: "High (3)"}[x],
        )
        submitted = st.form_submit_button("この内容で追加")

        if submitted:
            if not title.strip():
                st.warning("予定の内容を入力してください。")
            else:
                new_item = {
                    "title": title.strip(),
                    "priority": int(priority),
                    "created_at": datetime.now().isoformat(timespec="seconds"),
                }
                items.append(new_item)
                # ソートして保存
                sorted_items = sort_by_priority(items)
                save_schedule(sorted_items)
                st.success("予定を追加しました。")
                # 状態を即時反映するために再描画
                st.experimental_rerun()

    return items


def main() -> None:
    st.set_page_config(
        page_title="ゴージャス ToDo スケジュール",
        layout="wide",
    )
    apply_global_style()

    today = date.today()
    today_str = today.strftime("%Y-%m-%d")

    # データ読み込み
    items = sort_by_priority(load_schedule())
    high_count = sum(1 for i in items if int(i.get("priority", 1)) == 3)

    render_sidebar(today_str, len(items), high_count)

    st.markdown(
        """
        <h2 style="
            font-size: 2.2rem;
            font-weight: 700;
            letter-spacing: 0.08em;
            text-transform: uppercase;
            background: linear-gradient(90deg, #38bdf8, #a855f7, #f97316);
            -webkit-background-clip: text;
            color: transparent;
            margin-bottom: 1.2rem;
        ">
        Schedule Dashboard
        </h2>
        """,
        unsafe_allow_html=True,
    )

    left, right = st.columns((2, 1))

    with left:
        st.markdown("#### 重要度順の予定一覧")
        render_todo_list(items)

    with right:
        st.markdown('<div class="glass-panel">', unsafe_allow_html=True)
        render_add_form(items)
        st.markdown("</div>", unsafe_allow_html=True)


if __name__ == "__main__":
    main()

