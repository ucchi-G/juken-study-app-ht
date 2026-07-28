import json
import random
from pathlib import Path

import streamlit as st

st.set_page_config(page_title="高校受験トレーニング", page_icon="📘", layout="centered")

QUESTIONS_PER_SESSION = 10
questions_file = Path(__file__).parent / "questions.json"
with questions_file.open("r", encoding="utf-8") as file:
    all_questions = json.load(file)

categories = ["地理", "歴史", "公民"]

def reset_quiz(category):
    pool = [q for q in all_questions if q["category"] == category]
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

def reset_to_menu():
    for key in ["questions","question_index","score","answered","selected_answer","mistakes","study_mode","quiz_started","category"]:
        st.session_state.pop(key, None)
    st.rerun()

st.title("📘 高校受験トレーニング")

if not st.session_state.get("quiz_started", False):
    st.write("挑戦する分野を選んでください。各分野100問から毎回10問を出題します。")
    category = st.radio("分野", categories, horizontal=True)
    if st.button("この分野で始める", type="primary", use_container_width=True):
        reset_quiz(category)
        st.rerun()
    st.stop()

questions = st.session_state.questions
category = st.session_state.category
st.caption(f"選択中の分野：{category}")

if st.session_state.study_mode == "間違い直し":
    st.write("📝 間違えた問題にもう一度挑戦しよう！")
else:
    st.write(f"{category}の4択問題に挑戦しよう！")

if st.session_state.question_index >= len(questions):
    st.success("全問題が終了しました！")
    st.subheader(f"結果：{len(questions)}問中 {st.session_state.score}問正解")
    correct_rate = st.session_state.score / len(questions) * 100
    st.write(f"正答率：{correct_rate:.0f}%")

    if correct_rate == 100:
        st.balloons()
        st.write("🎉 全問正解です！" if st.session_state.study_mode == "通常問題" else "🎉 間違えた問題をすべて正解できました！")
    elif correct_rate >= 70:
        st.write("よくできました！")
    else:
        st.write("間違えた問題をもう一度確認してみましょう。")

    if st.session_state.mistakes:
        st.divider()
        st.subheader("📝 間違えた問題")
        for number, mistake in enumerate(st.session_state.mistakes, start=1):
            with st.expander(f"間違い {number}：{mistake['question']}"):
                st.write(f"あなたの答え：{mistake['selected_answer']}")
                st.write(f"正解：{mistake['answer']}")
                st.info(mistake["explanation"])

        if st.button("間違えた問題だけ再挑戦する", use_container_width=True):
            retry_questions = [{k: m[k] for k in ["id","category","question","choices","answer","explanation"]} for m in st.session_state.mistakes]
            st.session_state.questions = random.sample(retry_questions, len(retry_questions))
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
    if st.button(f"{category}をもう一度10問", use_container_width=True):
        reset_quiz(category)
        st.rerun()
    if st.button("分野選択に戻る", use_container_width=True):
        reset_to_menu()
else:
    current_question = questions[st.session_state.question_index]
    st.write(f"問題 {st.session_state.question_index + 1} / {len(questions)}")
    st.write(f"現在の正解数：{st.session_state.score}")
    st.progress((st.session_state.question_index + (1 if st.session_state.answered else 0)) / len(questions))
    st.subheader(current_question["question"])

    selected = st.radio(
        "答えを選んでください",
        current_question["choices"],
        index=None,
        disabled=st.session_state.answered,
        key=f"answer_{current_question['id']}_{st.session_state.study_mode}",
    )

    if not st.session_state.answered:
        if st.button("答え合わせ", type="primary", use_container_width=True):
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
        if st.session_state.selected_answer == current_question["answer"]:
            st.success("正解です！")
        else:
            st.error("不正解です。")
            st.write(f"正解は「{current_question['answer']}」です。")
        st.info(current_question["explanation"])
        if st.button("次の問題へ", type="primary", use_container_width=True):
            st.session_state.question_index += 1
            st.session_state.answered = False
            st.session_state.selected_answer = None
            st.rerun()

    st.divider()
    if st.button("学習を中断して分野選択に戻る"):
        reset_to_menu()
