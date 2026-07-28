import json
import random
import uuid
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
import streamlit as st


st.set_page_config(
    page_title="高校受験トレーニング",
    page_icon="📘",
    layout="centered",
)


# --------------------------------
# 基本設定
# --------------------------------
QUESTIONS_PER_SESSION = 10
USER_ID = "daughter"
JAPAN_TIMEZONE = ZoneInfo("Asia/Tokyo")

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

SUPABASE_HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json",
}


# --------------------------------
# 問題データを読み込む
# --------------------------------
questions_file = Path(__file__).parent / "questions.json"

with questions_file.open("r", encoding="utf-8") as file:
    all_questions = json.load(file)


categories = ["地理", "歴史", "公民"]


# --------------------------------
# Supabaseへ成績を保存
# --------------------------------
def save_study_result():
    """現在の学習結果をSupabaseへ1回だけ保存する。"""

    if st.session_state.get("result_saved", False):
        return True

    data = {
        "session_id": st.session_state.session_id,
        "user_id": USER_ID,
        "category": st.session_state.category,
        "total_count": len(st.session_state.questions),
        "correct_count": st.session_state.score,
        "study_mode": st.session_state.study_mode,
    }

    try:
        response = requests.post(
            f"{SUPABASE_URL}/rest/v1/study_results",
            headers={
                **SUPABASE_HEADERS,
                "Prefer": "return=minimal",
            },
            json=data,
            timeout=10,
        )

        response.raise_for_status()
        st.session_state.result_saved = True
        return True

    except requests.RequestException as error:
        st.session_state.save_error = str(error)
        return False


# --------------------------------
# Supabaseから全成績を取得
# --------------------------------
def fetch_study_results():
    """daughterの成績履歴をすべて取得する。"""

    try:
        response = requests.get(
            f"{SUPABASE_URL}/rest/v1/study_results",
            headers=SUPABASE_HEADERS,
            params={
                "select": (
                    "studied_at,category,total_count,"
                    "correct_count,study_mode"
                ),
                "user_id": f"eq.{USER_ID}",
                "order": "studied_at.desc",
            },
            timeout=10,
        )

        response.raise_for_status()
        return response.json(), None

    except requests.RequestException as error:
        return [], str(error)


# --------------------------------
# 成績を集計
# --------------------------------
def calculate_statistics(results):
    """本日・累計・分野別の成績を計算する。"""

    today = datetime.now(JAPAN_TIMEZONE).date()

    today_total = 0
    today_correct = 0
    all_total = 0
    all_correct = 0

    category_statistics = {
        "地理": {
            "total": 0,
            "correct": 0,
        },
        "歴史": {
            "total": 0,
            "correct": 0,
        },
        "公民": {
            "total": 0,
            "correct": 0,
        },
    }

    for result in results:
        total_count = result["total_count"]
        correct_count = result["correct_count"]
        category = result["category"]

        # 累計
        all_total += total_count
        all_correct += correct_count

        # 分野別
        if category in category_statistics:
            category_statistics[category]["total"] += total_count
            category_statistics[category]["correct"] += correct_count

        # 学習日の判定
        studied_at = datetime.fromisoformat(
            result["studied_at"].replace("Z", "+00:00")
        )
        studied_date = studied_at.astimezone(
            JAPAN_TIMEZONE
        ).date()

        # 本日分
        if studied_date == today:
            today_total += total_count
            today_correct += correct_count

    today_rate = (
        today_correct / today_total * 100
        if today_total > 0
        else 0
    )

    all_rate = (
        all_correct / all_total * 100
        if all_total > 0
        else 0
    )

    for category in category_statistics:
        category_total = category_statistics[category]["total"]
        category_correct = category_statistics[category]["correct"]

        category_statistics[category]["rate"] = (
            category_correct / category_total * 100
            if category_total > 0
            else 0
        )

    return {
        "today_total": today_total,
        "today_correct": today_correct,
        "today_rate": today_rate,
        "all_total": all_total,
        "all_correct": all_correct,
        "all_rate": all_rate,
        "categories": category_statistics,
    }

# --------------------------------
# 成績表示
# --------------------------------
def display_statistics():
    """本日・累計・分野別の成績を表示する。"""

    results, error = fetch_study_results()

    if error:
        st.warning("成績データを読み込めませんでした。")
        return

    statistics = calculate_statistics(results)

    st.subheader("📊 学習成績")

    today_column, all_column = st.columns(2)

    with today_column:
        st.markdown("#### 本日")

        st.metric(
            "正解数",
            (
                f"{statistics['today_correct']} / "
                f"{statistics['today_total']}問"
            ),
        )

        st.metric(
            "正答率",
            f"{statistics['today_rate']:.0f}%",
        )

    with all_column:
        st.markdown("#### これまで")

        st.metric(
            "正解数",
            (
                f"{statistics['all_correct']} / "
                f"{statistics['all_total']}問"
            ),
        )

        st.metric(
            "正答率",
            f"{statistics['all_rate']:.0f}%",
        )

    st.divider()
    st.markdown("#### 分野別の累計成績")

    geography_column, history_column, civics_column = (
        st.columns(3)
    )

    category_columns = {
        "地理": geography_column,
        "歴史": history_column,
        "公民": civics_column,
    }

    category_icons = {
        "地理": "🌏",
        "歴史": "🏯",
        "公民": "⚖️",
    }

    for category, column in category_columns.items():
        category_data = statistics["categories"][category]

        with column:
            st.markdown(
                f"##### {category_icons[category]} {category}"
            )

            st.metric(
                "正解数",
                (
                    f"{category_data['correct']} / "
                    f"{category_data['total']}問"
                ),
            )

            st.metric(
                "正答率",
                f"{category_data['rate']:.0f}%",
            )

# --------------------------------
# 新しい通常問題を開始
# --------------------------------
def reset_quiz(category):
    pool = [
        question
        for question in all_questions
        if question["category"] == category
    ]

    count = min(QUESTIONS_PER_SESSION, len(pool))

    st.session_state.questions = random.sample(pool, count)
    st.session_state.question_index = 0
    st.session_state.score = 0
    st.session_state.answered = False
    st.session_state.selected_answer = None
    st.session_state.mistakes = []
    st.session_state.study_mode = "通常問題"
    st.session_state.quiz_started = True
    st.session_state.category = category

    # 学習1回ごとの識別番号
    st.session_state.session_id = str(uuid.uuid4())

    # 成績の二重保存を防ぐ
    st.session_state.result_saved = False
    st.session_state.save_error = None


# --------------------------------
# 分野選択画面へ戻る
# --------------------------------
def reset_to_menu():
    keys = [
        "questions",
        "question_index",
        "score",
        "answered",
        "selected_answer",
        "mistakes",
        "study_mode",
        "quiz_started",
        "category",
        "session_id",
        "result_saved",
        "save_error",
    ]

    for key in keys:
        st.session_state.pop(key, None)

    st.rerun()


# --------------------------------
# タイトル
# --------------------------------
st.title("📘 高校受験トレーニング")


# --------------------------------
# 分野選択画面
# --------------------------------
if not st.session_state.get("quiz_started", False):
    display_statistics()

    st.divider()

    st.write(
        "挑戦する分野を選んでください。"
        "各分野100問から毎回10問を出題します。"
    )

    category = st.radio(
        "分野",
        categories,
        horizontal=True,
    )

    if st.button(
        "この分野で始める",
        type="primary",
        use_container_width=True,
    ):
        reset_quiz(category)
        st.rerun()

    st.stop()


# --------------------------------
# 学習中
# --------------------------------
questions = st.session_state.questions
category = st.session_state.category

st.caption(f"選択中の分野：{category}")

if st.session_state.study_mode == "間違い直し":
    st.write("📝 間違えた問題にもう一度挑戦しよう！")
else:
    st.write(f"{category}の4択問題に挑戦しよう！")


# --------------------------------
# 結果画面
# --------------------------------
if st.session_state.question_index >= len(questions):

    # 初回表示時だけSupabaseへ保存
    saved = save_study_result()

    st.success("全問題が終了しました！")

    st.subheader(
        f"結果：{len(questions)}問中 "
        f"{st.session_state.score}問正解"
    )

    correct_rate = (
        st.session_state.score / len(questions) * 100
    )

    st.write(f"正答率：{correct_rate:.0f}%")

    if saved:
        st.caption("学習結果を保存しました。")
    else:
        st.warning("学習結果を保存できませんでした。")

        if st.session_state.get("save_error"):
            with st.expander("エラー内容"):
                st.code(st.session_state.save_error)

    if correct_rate == 100:
        st.balloons()

        if st.session_state.study_mode == "通常問題":
            st.write("🎉 全問正解です！")
        else:
            st.write(
                "🎉 間違えた問題をすべて正解できました！"
            )

    elif correct_rate >= 70:
        st.write("よくできました！")

    else:
        st.write(
            "間違えた問題をもう一度確認してみましょう。"
        )

    st.divider()

    # 保存後の最新成績
    display_statistics()

    # --------------------------------
    # 間違えた問題
    # --------------------------------
    if st.session_state.mistakes:
        st.divider()
        st.subheader("📝 間違えた問題")

        for number, mistake in enumerate(
            st.session_state.mistakes,
            start=1,
        ):
            with st.expander(
                f"間違い {number}：{mistake['question']}"
            ):
                st.write(
                    f"あなたの答え："
                    f"{mistake['selected_answer']}"
                )
                st.write(
                    f"正解：{mistake['answer']}"
                )
                st.info(mistake["explanation"])

        if st.button(
            "間違えた問題だけ再挑戦する",
            use_container_width=True,
        ):
            retry_questions = []

            for mistake in st.session_state.mistakes:
                retry_questions.append(
                    {
                        key: mistake[key]
                        for key in [
                            "id",
                            "category",
                            "question",
                            "choices",
                            "answer",
                            "explanation",
                        ]
                    }
                )

            st.session_state.questions = random.sample(
                retry_questions,
                len(retry_questions),
            )
            st.session_state.question_index = 0
            st.session_state.score = 0
            st.session_state.answered = False
            st.session_state.selected_answer = None
            st.session_state.mistakes = []
            st.session_state.study_mode = "間違い直し"

            # 間違い直しも新しい学習記録として保存
            st.session_state.session_id = str(uuid.uuid4())
            st.session_state.result_saved = False
            st.session_state.save_error = None

            st.rerun()

    else:
        st.success("間違えた問題はありません！")

    st.divider()

    if st.button(
        f"{category}をもう一度10問",
        use_container_width=True,
    ):
        reset_quiz(category)
        st.rerun()

    if st.button(
        "分野選択に戻る",
        use_container_width=True,
    ):
        reset_to_menu()


# --------------------------------
# 問題画面
# --------------------------------
else:
    current_question = questions[
        st.session_state.question_index
    ]

    st.write(
        f"問題 {st.session_state.question_index + 1} "
        f"/ {len(questions)}"
    )

    st.write(
        f"現在の正解数：{st.session_state.score}"
    )

    progress = (
        st.session_state.question_index
        + (1 if st.session_state.answered else 0)
    ) / len(questions)

    st.progress(progress)

    st.subheader(current_question["question"])

    selected = st.radio(
        "答えを選んでください",
        current_question["choices"],
        index=None,
        disabled=st.session_state.answered,
        key=(
            f"answer_{current_question['id']}_"
            f"{st.session_state.study_mode}_"
            f"{st.session_state.session_id}"
        ),
    )

    if not st.session_state.answered:
        if st.button(
            "答え合わせ",
            type="primary",
            use_container_width=True,
        ):
            if selected is None:
                st.warning("答えを選んでください。")

            else:
                st.session_state.selected_answer = selected
                st.session_state.answered = True

                if selected == current_question["answer"]:
                    st.session_state.score += 1

                else:
                    mistake = current_question.copy()
                    mistake["selected_answer"] = selected
                    st.session_state.mistakes.append(mistake)

                st.rerun()

    else:
        if (
            st.session_state.selected_answer
            == current_question["answer"]
        ):
            st.success("正解です！")

        else:
            st.error("不正解です。")
            st.write(
                f"正解は「{current_question['answer']}」です。"
            )

        st.info(current_question["explanation"])

        if st.button(
            "次の問題へ",
            type="primary",
            use_container_width=True,
        ):
            st.session_state.question_index += 1
            st.session_state.answered = False
            st.session_state.selected_answer = None
            st.rerun()

    st.divider()

    if st.button("学習を中断して分野選択に戻る"):
        reset_to_menu()