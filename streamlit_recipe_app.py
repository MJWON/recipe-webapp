import streamlit as st
import pandas as pd

# --- Load Data ---
@st.cache_data
def load_data():
    recipe_df = pd.read_excel("최종_한식레시피_300개_수정버전.xlsx")
    expiry_df = pd.read_excel("한식재료_유통기한_전체정리_300개.xlsx")
    default_expiry = pd.Series(
        expiry_df["권장유통기한(일)"].values,
        index=expiry_df["재료명"]
    ).to_dict()
    return recipe_df, default_expiry

recipe_df, default_expiry_dict = load_data()

st.title("🍳 자취생 맞춤 한식 레시피 추천기")

# --- Input: User ingredients ---
st.subheader("1. 보유 재료 입력")

user_ingredients_expiry = {}
with st.form("ingredient_form"):
    cols = st.columns(2)
    with cols[0]:
        ingredients_input = st.text_area("보유 재료 (쉼표로 구분)", "김치,두부,계란,양파")
    with cols[1]:
        cook_time_limit = st.slider("⏱ 조리 가능 시간 (분)", min_value=5, max_value=60, value=20)
    submitted = st.form_submit_button("레시피 추천받기")

if submitted:
    input_ingredients = [i.strip() for i in ingredients_input.split(",") if i.strip() != ""]
    for ing in input_ingredients:
        expiry = default_expiry_dict.get(ing, None)
        user_ingredients_expiry[ing] = expiry

    # --- Recommend recipes ---
    recommendations = []
    for _, row in recipe_df.iterrows():
        name = row["이름"]
        ingredients = row["재료"].split(",")
        time = row["조리시간(분)"]
        steps = row["설명"]

        if time > cook_time_limit:
            continue

        matched = [i for i in ingredients if i in user_ingredients_expiry]
        match_ratio = len(matched) / len(ingredients)
        if match_ratio < 0.5:
            continue

        near_expiry = sum(
            user_ingredients_expiry[i] is not None and user_ingredients_expiry[i] <= 3
            for i in matched
        )
        missing = [i for i in ingredients if i not in user_ingredients_expiry]

        recommendations.append({
            "이름": name,
            "조리시간": time,
            "일치율": round(match_ratio * 100),
            "보유재료": matched,
            "부족재료": missing,
            "설명": steps,
            "임박재료수": near_expiry
        })

    # --- Remove duplicates ---
    seen = set()
    unique = []
    for r in recommendations:
        key = (r["이름"], tuple(sorted(r["보유재료"] + r["부족재료"])))
        if key not in seen:
            unique.append(r)
            seen.add(key)

    # --- Sort and Display ---
    sorted_rec = sorted(unique, key=lambda x: (-x["임박재료수"], -x["일치율"], x["조리시간"]))[:5]

    st.subheader("2. 추천 레시피")
    if not sorted_rec:
        st.warning("조건에 맞는 레시피가 없습니다.")
    else:
        for idx, rec in enumerate(sorted_rec, 1):
            with st.expander(f"[{idx}] {rec['이름']} (⏱ {rec['조리시간']}분, 일치율 {rec['일치율']}%)"):
                st.markdown(f"**✔️ 보유 재료:** {', '.join(rec['보유재료'])}")
                if rec['부족재료']:
                    st.markdown(f"**🛒 부족 재료:** {', '.join(rec['부족재료'])}")
                st.markdown(f"**🌡 유통기한 임박 재료 수:** {rec['임박재료수']}")
                st.markdown("---")
                st.markdown(f"📋 **조리법:**\n\n{rec['설명']}")
