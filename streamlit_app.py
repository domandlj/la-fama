import streamlit as st

st.title("🧉 La Fama (Minorista)")


st.number_input("Pick a number", 0, 10)

if st.button("Click me"):
    st.write("Button was clicked!")