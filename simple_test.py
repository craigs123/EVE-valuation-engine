import streamlit as st

st.set_page_config(page_title="Button Test", layout="wide")

st.title("Simple Button Test")

# Initialize session state
if 'click_count' not in st.session_state:
    st.session_state.click_count = 0

st.write("This is a minimal test to check if buttons work at all.")

# Simple button test
if st.button("Click Me!", key="test_btn"):
    st.session_state.click_count += 1
    st.balloons()

st.write(f"Button has been clicked {st.session_state.click_count} times")

# Test different button types
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Primary", type="primary"):
        st.success("Primary button works!")

with col2:
    if st.button("Secondary"):
        st.info("Secondary button works!")

with col3:
    if st.button("Disabled", disabled=True):
        st.error("This shouldn't show")

st.write("If you can see click counts increase and see success messages, buttons work fine.")