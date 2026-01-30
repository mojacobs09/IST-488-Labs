import streamlit as st


st.set_page_config(page_title = 'IST 488 Labs',
               initial_sidebar_state = 'expanded')
st.title ("IST 488 Labs")
lab1 = st.Page('Labs/Lab1.py', title = 'Lab 1')
lab2 = st.Page('Labs/Lab2.py', title = 'Lab 2', default = True)

pg = st.navigation([lab2, lab1])
pg.run()
