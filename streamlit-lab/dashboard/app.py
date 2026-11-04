import os
import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8001").rstrip("/")

st.set_page_config(page_title="DataCo Product Analytics", page_icon="📊", layout="wide")
st.title("DataCo | Product Analytics")
st.caption("Consultation d'une fiche produit alimentée par HBase")

with st.sidebar:
    st.header("Recherche")
    product_id = st.text_input("Product ID", value="1004")
    search = st.button("Afficher le produit", type="primary", use_container_width=True)
    st.divider()
    st.caption(f"API : {API_URL}")

if search:
    if not product_id.strip():
        st.warning("Saisissez un identifiant produit.")
    else:
        try:
            response = requests.get(
                f"{API_URL}/products/{product_id.strip()}/analytics", timeout=10
            )
            if response.status_code == 404:
                st.error("Aucun produit ne correspond à cet identifiant.")
            else:
                response.raise_for_status()
                product = response.json()
                st.subheader(product.get("product_name") or f"Produit {product_id}")
                left, right = st.columns(2)
                revenue = product.get("revenue")
                views = product.get("view_number")
                left.metric("Revenue", f"{float(revenue):,.2f}" if revenue else "N/A")
                right.metric("Views", f"{int(float(views)):,}" if views else "N/A")
                st.write("**Category ID :**", product.get("category_id") or "N/A")
                with st.expander("Données API brutes"):
                    st.json(product)
        except requests.RequestException as exc:
            st.error(f"Impossible de contacter l'API : {exc}")
        except (TypeError, ValueError):
            st.error("L'API a retourné une valeur numérique invalide.")

st.info("Saisissez un Product ID connu, par exemple 1004, puis cliquez sur Afficher le produit.")
