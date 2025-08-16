import streamlit as st

st.title("Button Test")

# Test basic button functionality
if st.button("Test Button"):
    st.success("Button clicked successfully!")
    st.write("This confirms Streamlit buttons work in this environment")

# Test session state
if 'test_counter' not in st.session_state:
    st.session_state.test_counter = 0

if st.button("Counter Button"):
    st.session_state.test_counter += 1

st.write(f"Counter: {st.session_state.test_counter}")