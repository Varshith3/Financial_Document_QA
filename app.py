import streamlit as st
from main import query_data

st.title("Financial Report QA")
st.markdown("Use this tool to ask questions about the loaded financial reports.")
query = st.text_area(
        "Enter your question:",
        placeholder="What was the revenue in Q1? How has the profit margin changed?"
    )

col1, col2 = st.columns([1,5])
with col1:
    submit_button = st.button("Submit", type="primary", use_container_width=True)

if submit_button and query:
        with st.spinner("Processing your query..."):
            try:
                answer = query_data(query)
                st.subheader("Answer")
                st.markdown(answer)
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")