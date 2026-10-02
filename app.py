import streamlit as st
from datetime import datetime
from analyzer import analyze_text, analyze_image

st.set_page_config(page_title="PrivacyLens", page_icon="🔐")
st.title("🔐 PrivacyLens")
st.caption("AI-Powered Privacy Checker")
st.info("Uploaded content is processed for analysis and is not intentionally stored by PrivacyLens.")

LEVELS = [
    ("high", "🔴 HIGH ATTENTION"),
    ("review", "🟡 REVIEW"),
    ("low", "🟢 LOWER SENSITIVITY"),
]


def build_report(result):
    items = result.get("items", [])
    high = [i for i in items if i.get("level") == "high"]
    review = [i for i in items if i.get("level") == "review"]
    low = [i for i in items if i.get("level") == "low"]

    lines = []
    lines.append("=" * 40)
    lines.append("PRIVACYLENS - PRIVACY REPORT")
    lines.append(datetime.now().strftime("Generated: %d %b %Y, %I:%M %p"))
    lines.append("=" * 40)
    lines.append("")
    lines.append(f"Items detected: {len(items)}")
    lines.append(f"  High attention: {len(high)}")
    lines.append(f"  Review: {len(review)}")
    lines.append(f"  Lower sensitivity: {len(low)}")
    lines.append("")
    lines.append(f"Summary: {result.get('summary', '')}")
    lines.append("")

    for title, group in (("HIGH ATTENTION", high), ("REVIEW", review), ("LOWER SENSITIVITY", low)):
        if group:
            lines.append(title)
            lines.append("-" * 40)
            for i in group:
                lines.append(f"* {i.get('item', '')} [{i.get('category', '')}]")
                lines.append(f"  Why: {i.get('why', '')}")
                lines.append(f"  Consider: {i.get('suggestion', '')}")
            lines.append("")

    recommended = high + review
    if recommended:
        lines.append("RECOMMENDED REVIEW")
        lines.append("-" * 40)
        for n, i in enumerate(recommended, 1):
            lines.append(f"{n}. {i.get('item', '')}")
        lines.append("")

    lines.append("Sensitive values are masked. No image or text is stored by PrivacyLens.")
    return "\n".join(lines)


def show_results(result):
    items = result.get("items", [])
    st.subheader("🔐 Privacy Analysis")
    st.write(result.get("summary", ""))

    if not items:
        st.success("No sensitive information detected.")
        return

    high = sum(1 for i in items if i.get("level") == "high")
    review = sum(1 for i in items if i.get("level") == "review")
    low = sum(1 for i in items if i.get("level") == "low")

    st.markdown("### 📊 Privacy Report")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Detected", len(items))
    c2.metric("🔴 High", high)
    c3.metric("🟡 Review", review)
    c4.metric("🟢 Lower", low)

    for level_key, level_title in LEVELS:
        group = [i for i in items if i.get("level") == level_key]
        if group:
            st.markdown(f"### {level_title}")
            for item in group:
                label = f"{item.get('item', 'Item')} ({item.get('category', '')})"
                with st.expander(label, expanded=(level_key == "high")):
                    st.write(f"**Why it matters:** {item.get('why', '')}")
                    st.write(f"**Consider:** {item.get('suggestion', '')}")

    to_review = [i for i in items if i.get("level") in ("high", "review")]
    if to_review:
        st.markdown("### 💡 BEFORE SHARING")
        for item in to_review:
            st.write(f"✓ {item.get('suggestion', '')}")

    st.download_button(
        label="⬇️ Download report",
        data=build_report(result),
        file_name="privacylens_report.txt",
        mime="text/plain",
    )


tab_image, tab_text = st.tabs(["📸 Image", "📝 Text"])

with tab_image:
    uploaded = st.file_uploader(
        "Upload a screenshot or document image",
        type=["png", "jpg", "jpeg", "webp"],
    )
    if uploaded is not None:
        st.image(uploaded, caption="Your upload", use_container_width=True)
    if st.button("Check Privacy", key="check_image"):
        if uploaded is None:
            st.warning("Please upload an image first.")
        else:
            st.session_state["result"] = None
            with st.spinner("Analyzing image..."):
                try:
                    st.session_state["result"] = analyze_image(uploaded.getvalue(), uploaded.type)
                except Exception as e:
                    st.error(f"Something went wrong: {e}")

with tab_text:
    user_text = st.text_area("Paste text to check", height=180)
    if st.button("Check Privacy", key="check_text"):
        if not user_text.strip():
            st.warning("Please paste some text first.")
        else:
            st.session_state["result"] = None
            with st.spinner("Analyzing text..."):
                try:
                    st.session_state["result"] = analyze_text(user_text)
                except Exception as e:
                    st.error(f"Something went wrong: {e}")

if st.session_state.get("result"):
    show_results(st.session_state["result"])