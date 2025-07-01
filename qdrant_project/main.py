import streamlit as st
import requests

# Streamlit frontend
st.title("Product Support Chatbot")

st.write("""
    Ask any question about your product
""")

# Textbox to enter customer query
query = st.text_input("Ask your question:")

# Button to submit query
if st.button('Ask'):
    if query:
        try:
            # Send the user query to the Flask backend
            response = requests.post("http://localhost:5000/query", json={"query": query})
            
            # If the response is successful, display the answer
            if response.status_code == 200:
                result = response.json()
                if result:
                    st.write("Here are the top 5 relevant results:")
                    for idx, res in enumerate(result):
                        st.write(f"**Answer {idx+1}:** {res['content']} (Score: {res['score']:.2f})")
                else:
                    st.write("Sorry, I couldn't find any relevant information.")
            else:
                st.write(f"Error: {response.status_code} - {response.text}")
        except Exception as e:
            st.write(f"An error occurred: {str(e)}")
    else:
        st.write("Please enter a question.")
