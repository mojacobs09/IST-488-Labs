import streamlit as st


st.set_page_config(page_title = 'IST 488 Labs',
               initial_sidebar_state = 'expanded')
st.title ("IST 488 Labs")
lab1 = st.Page('Labs/Lab1.py', title = 'Lab 1')
lab2 = st.Page('Labs/Lab2.py', title = 'Lab 2')
lab3 = st.Page('Labs/Lab3.py', title = 'Lab 3')
lab4 = st.Page('Labs/Lab4.py', title = 'Lab 4')
lab5 = st.Page('Labs/Lab5.py', title = 'Lab 5')
lab6 = st.Page('Labs/Lab6.py', title = 'Lab 6')
lab7 = st.Page('Labs/Lab7.py', title = 'Lab 7', default = True)
pg = st.navigation([lab7, lab6, lab5, lab4, lab3, lab2, lab1])
pg.run()
