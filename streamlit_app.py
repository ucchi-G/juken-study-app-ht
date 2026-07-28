import json
import random
from pathlib import Path

import streamlit as st


st.set_page_config(
    page_title="高校受験トレーニング",
    page_icon="📘",
    layout="centered",
)


# -----------------------------
# 問題データをJSONから読み込む
# -----------------------------
questions_file = Path(__file__).parent / "questions.json"

with questions_file.open("r", encoding="utf-8") as file:
    original_questions = json.load(file)


# -----------------------------
# セッション状態の初期化
# -----------------------------
if "questions" not in st.session_state:
    st.session_state.questions = random.sample(
        original_questions,
        len(original_questions),
    )

if "question_index" not in st.session_state:
    st.session_state.question_index = 0

if "score" not in st.session_state:
    st.session_state.score = 0

if "answered" not in st.session_state:
    st.session_state.answered = False

if "selected_answer" not in st.session_state:
    st.session_state.selected_answer = None

if "mistakes" not in st.session_state:
    st.session_state.mistakes = []

if "study_mode" not in st.session_state:
    st.session_state.study_mode = "通常問題"


questions = st.session_state.questions


# -----------------------------
# タイトル
# -----------------------------
st.title("📘 高校受験トレーニング")

if st.session_state.study_mode == "間違い直し":
    st.write("📝 間違えた問題にもう一度挑戦しよう！")
else:
    st.write("社会の4択問題に挑戦しよう！")


# -----------------------------
# 全問題終了後の結果画面
# -----------------------------
if st.session_state.question_index >= len(questions):
    st.success("全問題が終了しました！")

    st.subheader(
        f"結果：{len(questions)}問中 "
        f"{st.session_state.score}問正解"
    )

    correct_rate = st.session_state.score / len(questions) * 100
    st.write(f"正答率：{correct_rate:.0f}%")

    if correct_rate == 100:
        st.balloons()

        if st.session_state.study_mode == "間違い直し":
            st.write("🎉 間違えた問題をすべて正解できました！")
        else:
            st.write("🎉 全問正解です！")

    elif correct_rate >= 70:
        st.write("よくできました！")

    else:
        st.write("間違えた問題をもう一度確認してみましょう。")

    # -----------------------------
    # 間違えた問題の一覧
    # -----------------------------
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

        # -----------------------------
        # 間違えた問題だけ再挑戦
        # -----------------------------
        if st.button("間違えた問題だけ再挑戦する"):
            retry_questions = []

            for mistake in st.session_state.mistakes:
                retry_questions.append(
                    {
                        "question": mistake["question"],
                        "choices": mistake["choices"],
                        "answer": mistake["answer"],
                        "explanation": mistake["explanation"],
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

            st.rerun()

    else:
        st.success("間違えた問題はありません！")

    st.divider()

    # -----------------------------
    # 最初からもう一度挑戦
    # -----------------------------
    if st.button("全問題にもう一度挑戦する"):
        st.session_state.questions = random.sample(
            original_questions,
            len(original_questions),
        )

        st.session_state.question_index = 0
        st.session_state.score = 0
        st.session_state.answered = False
        st.session_state.selected_answer = None
        st.session_state.mistakes = []
        st.session_state.study_mode = "通常問題"

        st.rerun()


# -----------------------------
# 問題画面
# -----------------------------
else:
    current_question = questions[st.session_state.question_index]

    st.write(
        f"問題 {st.session_state.question_index + 1} "
        f"/ {len(questions)}"
    )

    st.write(f"現在の正解数：{st.session_state.score}")

    st.progress(
        st.session_state.question_index / len(questions)
    )

    st.subheader(current_question["question"])

    selected = st.radio(
        "答えを選んでください",
        current_question["choices"],
        index=None,
        disabled=st.session_state.answered,
        key=f"question_{st.session_state.study_mode}_"
        f"{st.session_state.question_index}",
    )

    if not st.session_state.answered:
        if st.button("答え合わせ"):
            if selected is None:
                st.warning("答えを選んでください。")

            else:
                st.session_state.selected_answer = selected
                st.session_state.answered = True

                if selected == current_question["answer"]:
                    st.session_state.score += 1

                else:
                    st.session_state.mistakes.append(
                        {
                            "question": current_question[
                                "question"
                            ],
                            "choices": current_question[
                                "choices"
                            ],
                            "answer": current_question[
                                "answer"
                            ],
                            "explanation": current_question[
                                "explanation"
                            ],
                            "selected_answer": selected,
                        }
                    )

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

        if st.button("次の問題へ"):
            st.session_state.question_index += 1
            st.session_state.answered = False
            st.session_state.selected_answer = None

            st.rerun()