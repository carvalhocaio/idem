import streamlit as st

st.set_page_config(page_title="idem", layout="wide")


def logout():
    st.write("in progress..")


pages = {
    "Your account": [
        st.Page(logout, title="Log out", icon=":material/logout:"),
    ],
    "Oracle": [
        st.Page(
            "oracle_cloud_infrastructure/instances.py",
            title="Instances",
            icon=":material/computer:",
        ),
    ],
}

pg = st.navigation(pages)
pg.run()
