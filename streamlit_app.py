import streamlit as st

st.set_page_config(
    page_title="高校受験トレーニング",
    page_icon="📘",
    layout="centered",
)

# 問題データ
questions = [
    {
        "question": "日本で最も面積が大きい都道府県はどこですか？",
        "choices": ["北海道", "岩手県", "長野県", "福島県"],
        "answer": "北海道",
        "explanation": "北海道は、日本の都道府県の中で最も面積が大きい地域です。",
    },
    {
        "question": "日本国憲法が施行された年はいつですか？",
        "choices": ["1945年", "1946年", "1947年", "1950年"],
        "answer": "1947年",
        "explanation": "日本国憲法は1946年11月3日に公布され、1947年5月3日に施行されました。",
    },
    {
        "question": "日本で最も長い川はどれですか？",
        "choices": ["利根川", "石狩川", "信濃川", "北上川"],
        "answer": "信濃川",
        "explanation": "信濃川は全長約367kmで、日本で最も長い川です。",
    },
]

# セッション状態の初期化
if "question_index" not in st.session_state:
    st.session_state.question_index = 0

if "score" not in st.session_state:
    st.session_state.score = 0

if "answered" not in st.session_state:
    st.session_state.answered = False

if "selected_answer" not in st.session_state:
    st.session_state.selected_answer = None

# タイトル
st.title("📘 高校受験トレーニング")
st.write("社会の4択問題に挑戦しよう！")

# 全問題終了後
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
        st.write("🎉 全問正解です！")
    elif correct_rate >= 70:
        st.write("よくできました！")
    else:
        st.write("間違えた問題をもう一度確認してみましょう。")

    if st.button("もう一度挑戦する"):
        st.session_state.question_index = 0
        st.session_state.score = 0
        st.session_state.answered = False
        st.session_state.selected_answer = None
        st.rerun()

else:
    # 現在の問題
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
        key=f"question_{st.session_state.question_index}",
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