import streamlit as st
from Type_Inferer_Controller import Type_Inferer_Controller

# Archivo principal para la interaccion con streamlit
tic = Type_Inferer_Controller()

st.title = 'Type Inferer'

def load_data(dir : str = 'file.txt', force_open = True):
    try:
        file = open(dir, 'r+')
    except FileNotFoundError:
        if force_open:
            file = open(dir, 'w+')
            file.close()
            file = open(dir, 'r+')
        else:
            return ''
    data = file.read()
    file.close()
    return data
def save_data(text : str, dir : str = 'file.txt'):
    file = open(dir, 'w+')
    file.write(text)
    file.close()

code = load_data()
if code:
    analysis = tic(code)
    for i in analysis:
        print(i)

sidebar_option = st.sidebar.radio(
    'Select what do you want to do:',
    (
        'See Code',
        'Insert Code',
        'Analyse Code',
        'Load file',
        'Save file'
    )
)

if sidebar_option == 'See Code':
    code = load_data()
    if code:
        st.code(code)
    else:
        st.markdown('Nothing to show')
elif sidebar_option == 'Insert Code':
    code = st.text_area('Insert your code here')
    if code != '':
        save_data(code)
elif sidebar_option == 'Analyse Code':
    code = load_data()
    if code:
        analysis = tic(code)
        for i in analysis:
            st.code(i)
    else:
        st.markdown('Insert code to analyse first')
elif sidebar_option == 'Load file':
    dir = st.text_input('Write the adress of the file you want to load here')
    if dir != '':
        code = load_data(dir, force_open=False)
        if code != '' and not code:
            st.markdown('File does not exists or is empty')
        else:
            save_data(code)
if sidebar_option == 'Save file':
    code = load_data()
    dir = st.text_input('Write the full adress where you want to save the file')
    if dir != '':
        try:
            save_data(code, dir)
            sidebar_option = 'See Code'
        except:
            st.markdown('Not valid direction')
