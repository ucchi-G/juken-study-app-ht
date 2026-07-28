import streamlit as st

st.set_page_config(
    page_title="高校受験トレーニング",
    page_icon="📘",
    layout="centered",
)

st.title("📘 高校受験トレーニング")
st.write("社会の4択問題に挑戦しよう！")

st.subheader("第1問")
st.write("日本で最も面積が大きい都道府県はどこですか？")

answer = st.radio(
    "答えを選んでください",
    ["北海道", "岩手県", "長野県", "福島県"],
    index=None,
)

if st.button("答え合わせ"):
    if answer is None:
        st.warning("答えを選んでください。")
    elif answer == "北海道":
        st.success("正解です！")
        st.info("北海道は、日本で最も面積が大きい都道府県です。")
    else:
        st.error("不正解です。")
        st.info("正解は北海道です。")