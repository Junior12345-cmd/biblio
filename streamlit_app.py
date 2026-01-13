import streamlit as st
from rdflib import Graph, URIRef, Namespace, RDF, RDFS, OWL, Literal
import pandas as pd
import os

# Configuration de la page
st.set_page_config(
    page_title="Gestion de Bibliothèque - Ontologie",
    page_icon="📚",
    layout="wide"
)

# Titre de l'application
st.title("📚 Système de Gestion de Bibliothèque avec Ontologie")
st.markdown("---")

# Initialiser le graphe RDF
g = Graph()

# Définir les nomspaces
BIB = Namespace("http://www.semanticweb.org/junior/ontologies/2026/0/bibliotheque#")

# Charger l'ontologie avec gestion d'erreur
def load_ontology():
    ontology_files = ["bibliotheque.ttl", "bibio.ttl", "ontology.ttl"]
    
    for file in ontology_files:
        if os.path.exists(file):
            try:
                g.parse(file, format="turtle")
                st.success(f"✅ Ontologie chargée : {file}")
                return True
            except Exception as e:
                st.error(f"Erreur lors du chargement de {file}: {str(e)}")
                return False
    
    # Si aucun fichier n'est trouvé
    st.warning("Aucun fichier d'ontologie trouvé. Téléchargez votre fichier .ttl")
    
    uploaded_file = st.file_uploader(
        "Téléchargez votre fichier d'ontologie (.ttl)", 
        type=['ttl'],
        help="Format Turtle attendu"
    )
    
    if uploaded_file is not None:
        try:
            # Sauvegarder temporairement le fichier
            with open("temp_ontology.ttl", "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            g.parse("temp_ontology.ttl", format="turtle")
            st.success("✅ Ontologie chargée depuis le fichier téléchargé")
            return True
        except Exception as e:
            st.error(f"Erreur lors du chargement : {str(e)}")
            return False
    
    return False

# Interface principale
if load_ontology():
    
    # Barre latérale pour la navigation
    st.sidebar.title("📖 Navigation")
    page = st.sidebar.radio(
        "Choisir une section :",
        ["🏠 Accueil", "📚 Liste des Livres", "👥 Utilisateurs", "🔄 Emprunts", "🔍 Requêtes SPARQL"]
    )
    
    if page == "🏠 Accueil":
        st.header("Tableau de bord")
        
        # Statistiques
        col1, col2, col3, col4 = st.columns(4)
        
        # Compter les livres
        query_livres = """
        PREFIX bib: <http://www.semanticweb.org/junior/ontologies/2026/0/bibliotheque#>
        SELECT (COUNT(?livre) as ?count)
        WHERE {
            ?livre a bib:Livre .
        }
        """
        
        try:
            results = g.query(query_livres)
            for row in results:
                with col1:
                    st.metric("Livres", row.count)
        except:
            with col1:
                st.metric("Livres", "0")
        
        # Ajouter d'autres métriques...
        
        # Aperçu de l'ontologie
        st.subheader("Aperçu de l'ontologie")
        st.write(f"Nombre de triplets : {len(g)}")
        
        # Afficher quelques triplets
        if st.checkbox("Afficher quelques triplets"):
            df_triples = pd.DataFrame(
                [(str(s), str(p), str(o)) for s, p, o in list(g)[:20]],
                columns=["Sujet", "Prédicat", "Objet"]
            )
            st.dataframe(df_triples)
    
    elif page == "📚 Liste des Livres":
        st.header("Liste des Livres")
        
        # Requête SPARQL pour les livres
        query = """
        PREFIX bib: <http://www.semanticweb.org/junior/ontologies/2026/0/bibliotheque#>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        
        SELECT ?livre ?titre ?auteur ?datePub
        WHERE {
            ?livre rdf:type bib:Livre .
            ?livre bib:titre ?titre .
            OPTIONAL { ?livre bib:auteur ?auteur . }
            OPTIONAL { ?livre bib:datePublication ?datePub . }
        }
        ORDER BY ?titre
        """
        
        try:
            results = g.query(query)
            
            if results:
                data = []
                for row in results:
                    data.append({
                        "Titre": str(row.titre) if row.titre else "N/A",
                        "Auteur": str(row.auteur) if row.auteur else "N/A",
                        "Date Publication": str(row.datePub) if row.datePub else "N/A",
                        "URI": str(row.livre)
                    })
                
                df = pd.DataFrame(data)
                st.dataframe(df[["Titre", "Auteur", "Date Publication"]])
                
                # Export CSV
                csv = df.to_csv(index=False)
                st.download_button(
                    label="📥 Télécharger la liste (CSV)",
                    data=csv,
                    file_name="livres_bibliotheque.csv",
                    mime="text/csv"
                )
            else:
                st.info("Aucun livre trouvé dans l'ontologie")
                
        except Exception as e:
            st.error(f"Erreur lors de l'exécution de la requête : {str(e)}")
    
    elif page == "🔍 Requêtes SPARQL":
        st.header("Requêtes SPARQL")
        
        # Requêtes prédéfinies
        st.subheader("Requêtes prédéfinies")
        
        queries = {
            "Tous les livres": """
            PREFIX bib: <http://www.semanticweb.org/junior/ontologies/2026/0/bibliotheque#>
            SELECT ?livre ?titre ?auteur WHERE {
                ?livre a bib:Livre .
                ?livre bib:titre ?titre .
                OPTIONAL { ?livre bib:auteur ?auteur . }
            }
            """,
            "Livres disponibles": """
            PREFIX bib: <http://www.semanticweb.org/junior/ontologies/2026/0/bibliotheque#>
            SELECT ?livre ?titre WHERE {
                ?livre a bib:Livre .
                ?livre bib:titre ?titre .
                ?livre bib:estDisponible true .
            }
            """,
            "Emprunts actifs": """
            PREFIX bib: <http://www.semanticweb.org/junior/ontologies/2026/0/bibliotheque#>
            SELECT ?emprunt ?livre ?utilisateur ?date WHERE {
                ?emprunt a bib:Emprunt .
                ?emprunt bib:concerneLivre ?livre .
                OPTIONAL { ?emprunt bib:effectuéPar ?utilisateur . }
                OPTIONAL { ?emprunt bib:dateEmprunt ?date . }
            }
            """
        }
        
        selected_query = st.selectbox("Choisir une requête :", list(queries.keys()))
        
        if st.button("Exécuter la requête"):
            with st.spinner("Exécution en cours..."):
                try:
                    results = g.query(queries[selected_query])
                    
                    if results:
                        data = []
                        for row in results:
                            row_dict = {}
                            for i, var in enumerate(results.vars):
                                value = row[i]
                                row_dict[var] = str(value) if value else ""
                            data.append(row_dict)
                        
                        df = pd.DataFrame(data)
                        st.dataframe(df)
                    else:
                        st.info("Aucun résultat trouvé")
                        
                except Exception as e:
                    st.error(f"Erreur SPARQL : {str(e)}")
        
        # Éditeur SPARQL personnalisé
        st.subheader("Éditeur SPARQL personnalisé")
        custom_query = st.text_area(
            "Écrivez votre requête SPARQL :",
            height=150,
            placeholder="Exemple : SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10"
        )
        
        if st.button("Exécuter ma requête") and custom_query.strip():
            try:
                results = g.query(custom_query)
                
                if results:
                    data = []
                    for row in results:
                        row_dict = {}
                        for i, var in enumerate(results.vars):
                            value = row[i]
                            row_dict[var] = str(value) if value else ""
                        data.append(row_dict)
                    
                    df = pd.DataFrame(data)
                    st.dataframe(df)
                else:
                    st.info("Aucun résultat trouvé")
                    
            except Exception as e:
                st.error(f"Erreur SPARQL : {str(e)}")

else:
    st.info("👈 Veuillez charger une ontologie pour commencer")

# Pied de page
st.markdown("---")
st.markdown("📚 Système de gestion de bibliothèque basé sur une ontologie RDF/OWL")