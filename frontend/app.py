import streamlit as st
import requests
import pandas as pd

API_URL = "http://localhost:8000"

st.set_page_config(
    page_title="DataTalk",
    page_icon="💬",
    layout="wide"
)

if "messages" not in st.session_state:
    st.session_state.messages = []

with st.sidebar:
    st.header("Vos données")
    uploaded_file = st.file_uploader(
        "Importez un fichier CSV ou Excel",
        type=["csv", "xlsx"]
    )
    if uploaded_file is not None:
        st.success(f"**{uploaded_file.name}**")
        if st.button("Effacer la conversation"):
            st.session_state.messages = []
            st.rerun()

st.title("DataTalk")
st.caption("Interrogez vos données en langage naturel")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.write(message["content"])
        if message.get("dataframe"):
            df_result = pd.DataFrame(message["dataframe"])
            st.dataframe(df_result, use_container_width=True)
        if message.get("figure"):
            import plotly.io as pio
            fig = pio.from_json(message["figure"])
            st.plotly_chart(fig, use_container_width=True)

if uploaded_file is None:
    st.info("Commencez par importer un fichier CSV ou Excel dans le panneau latéral pour pouvoir poser vos questions.")

question = st.chat_input(
    "Posez votre question sur vos données...",
    disabled=uploaded_file is None
)

if question and uploaded_file is not None:
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.write(question)

    with st.chat_message("assistant"):
        with st.spinner("Analyse en cours..."):
            try:
                response = requests.post(
                    f"{API_URL}/analyze",
                    data={"question": question},
                    files={"file": (uploaded_file.name, uploaded_file.getvalue())},
                    timeout=60,
                )
                if response.status_code == 200:
                    result = response.json()
                    st.write(result["text"])
                    if result.get("dataframe"):
                        df_result = pd.DataFrame(result["dataframe"])
                        st.dataframe(df_result, use_container_width=True)
                    if result.get("figure"):
                        import plotly.io as pio
                        fig = pio.from_json(result["figure"])
                        st.plotly_chart(fig, use_container_width=True)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result["text"],
                        "dataframe": result.get("dataframe", False),
                        "figure": result.get("figure", False),
                    })
                else:
                    detail = response.json().get("detail", "Erreur inconnue")
                    st.error(f"Erreur API : {detail}")
            except requests.exceptions.ConnectionError:
                st.error("Impossible de joindre l'API. Vérifiez que le serveur est démarré sur localhost:8000.")
            except requests.exceptions.Timeout:
                st.error("La requête a expiré. L'analyse prend trop de temps.")
