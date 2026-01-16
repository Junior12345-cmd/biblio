import streamlit as st
from rdflib import Graph, URIRef, Namespace, RDF, RDFS, OWL, Literal
import pandas as pd
import matplotlib.pyplot as plt
import os

# ================================
# FONCTIONS UTILITAIRES
# ================================

def detect_ontology_structure(g):
    """Détecte automatiquement la structure de l'ontologie"""
    structure = {
        'main_prefix': None,
        'main_namespace': None,
        'classes': {},
        'instances_by_class': {}
    }
    
    # Détecter le namespace principal
    namespace_counts = {}
    for s, p, o in g:
        for uri in [s, p]:
            if isinstance(uri, URIRef):
                uri_str = str(uri)
                if '#' in uri_str:
                    namespace = uri_str.split('#')[0] + '#'
                else:
                    parts = uri_str.split('/')
                    if len(parts) > 1:
                        namespace = '/'.join(parts[:-1]) + '/'
                    else:
                        namespace = uri_str
                namespace_counts[namespace] = namespace_counts.get(namespace, 0) + 1
    
    # Trouver le namespace le plus utilisé
    standard_namespaces = [
        'http://www.w3.org/1999/02/22-rdf-syntax-ns#',
        'http://www.w3.org/2000/01/rdf-schema#',
        'http://www.w3.org/2002/07/owl#',
        'http://www.w3.org/2001/XMLSchema#'
    ]
    
    for ns, count in sorted(namespace_counts.items(), key=lambda x: x[1], reverse=True):
        if ns not in standard_namespaces and count > 5:
            structure['main_namespace'] = ns
            break
    
    # Détecter le préfixe
    if structure['main_namespace']:
        for prefix, namespace in g.namespaces():
            if str(namespace) == structure['main_namespace']:
                structure['main_prefix'] = prefix
                break
    
    if not structure['main_prefix'] and structure['main_namespace']:
        structure['main_prefix'] = 'ont'
    
    # Détecter toutes les classes
    query_classes = """
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    SELECT ?class ?label WHERE {
        ?class a owl:Class .
        OPTIONAL { ?class rdfs:label ?label . }
    }
    """
    
    for row in g.query(query_classes):
        class_uri = row[0]
        label = str(row[1]) if row[1] else class_uri.split('#')[-1] if '#' in str(class_uri) else class_uri.split('/')[-1]
        structure['classes'][str(class_uri)] = {
            'label': label,
            'local_name': format_uri(class_uri)
        }
    
    # Compter les instances par classe
    for class_uri in structure['classes']:
        query_count = f"""
        SELECT (COUNT(?instance) as ?count) WHERE {{
            ?instance a <{class_uri}> .
        }}
        """
        try:
            result = list(g.query(query_count))[0]
            count = int(result[0])
            structure['instances_by_class'][class_uri] = count
        except:
            structure['instances_by_class'][class_uri] = 0
    
    return structure

def format_uri(uri):
    """Formate une URI pour l'affichage"""
    if isinstance(uri, URIRef):
        uri_str = str(uri)
        if '#' in uri_str:
            fragment = uri_str.split('#')[-1]
            if fragment:
                return fragment
        if '/' in uri_str:
            parts = uri_str.rstrip('/').split('/')
            last_part = parts[-1]
            if last_part:
                return last_part
        return uri_str
    elif isinstance(uri, Literal):
        return str(uri)
    return str(uri)

def load_ontology(file_path):
    """Charge une ontologie"""
    g = Graph()
    try:
        if file_path.endswith('.ttl'):
            g.parse(file_path, format='turtle')
        elif file_path.endswith('.rdf') or file_path.endswith('.owl'):
            g.parse(file_path, format='xml')
        else:
            g.parse(file_path)
        return g
    except Exception as e:
        st.error(f"Erreur de chargement: {e}")
        return None

# ================================
# INTERFACE STREAMLIT
# ================================

def main():
    st.set_page_config(
        page_title="Ontologie Bibliothèque",
        page_icon="📚",
        layout="wide"
    )
    
    st.title("📚 Système d'Analyse d'Ontologie Bibliothèque")
    
    # ===== SECTION IMPORT =====
    st.sidebar.header("📁 Importation de l'ontologie")
    
    # Upload fichier uniquement
    uploaded_file = st.sidebar.file_uploader(
        "Choisir un fichier d'ontologie",
        type=['ttl', 'rdf', 'owl'],
        help="Supporte: Turtle (.ttl), RDF/XML (.rdf, .owl)"
    )
    
    g = None
    file_info = None
    
    if uploaded_file:
        # Sauvegarder temporairement
        temp_path = f"temp_{uploaded_file.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        g = load_ontology(temp_path)
        file_info = {
            'name': uploaded_file.name,
            'path': temp_path
        }
    
    # ===== SI ONTOLOGIE CHARGÉE =====
    if g and len(g) > 0:
        # Détecter la structure
        with st.spinner("Analyse de l'ontologie en cours..."):
            structure = detect_ontology_structure(g)
        
        # ===== SIDEBAR: INFORMATIONS =====
        st.sidebar.header("📋 Informations")
        
        if structure['main_namespace']:
            st.sidebar.success(f"**Namespace principal:**\n`{structure['main_namespace']}`")
        
        st.sidebar.metric("Triplets RDF", len(g))
        st.sidebar.metric("Classes", len(structure['classes']))
        
        total_instances = sum(structure['instances_by_class'].values())
        st.sidebar.metric("Instances totales", total_instances)
        
        # ===== PAGES PRINCIPALES =====
        st.sidebar.header("Navigation")
        page = st.sidebar.radio(
            "Pages:",
            ["🏠 Tableau de bord", "👁️ Explorer", "🔍 Requêtes SPARQL"]
        )
        
        # Bind le namespace principal
        if structure['main_prefix'] and structure['main_namespace']:
            ONT = Namespace(structure['main_namespace'])
            g.bind(structure['main_prefix'], ONT)
        
        # ===== PAGE: TABLEAU DE BORD =====
        if page == "🏠 Tableau de bord":
            st.header("Tableau de bord de l'ontologie")
            
            # Métriques principales
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Triplets", len(g))
            
            with col2:
                st.metric("Classes", len(structure['classes']))
            
            with col3:
                st.metric("Instances", total_instances)
            
            # Répartition des instances par classe (sans graphique)
            st.subheader("Répartition des instances par classe")
            
            if structure['instances_by_class']:
                # Tableau des classes
                classes_data = []
                for class_uri, count in structure['instances_by_class'].items():
                    class_name = structure['classes'].get(class_uri, {}).get('label', format_uri(class_uri))
                    classes_data.append({
                        'Classe': class_name,
                        'Instances': count,
                        'URI': class_uri
                    })
                
                df_classes = pd.DataFrame(classes_data).sort_values('Instances', ascending=False)
                
                # Afficher le tableau
                st.dataframe(df_classes, use_container_width=True, hide_index=True)
                
                # Téléchargement CSV
                csv = df_classes.to_csv(index=False)
                st.download_button(
                    "📥 Télécharger CSV",
                    csv,
                    "classes_instances.csv",
                    "text/csv"
                )
            else:
                st.info("Aucune instance trouvée dans l'ontologie")
        
        # ===== PAGE: EXPLORER =====
        elif page == "👁️ Explorer":
            st.header("Exploration de l'ontologie")
            
            tab1, tab2 = st.tabs(["Classes", "Instances"])
            
            with tab1:
                st.subheader("Classes de l'ontologie")
                
                # Filtre de recherche
                search_class = st.text_input("Rechercher une classe:", "")
                
                classes_to_show = []
                for class_uri, class_info in structure['classes'].items():
                    if not search_class or search_class.lower() in class_info['label'].lower():
                        classes_to_show.append({
                            'Label': class_info['label'],
                            'URI': class_uri,
                            'Instances': structure['instances_by_class'].get(class_uri, 0)
                        })
                
                if classes_to_show:
                    df_classes = pd.DataFrame(classes_to_show)
                    st.dataframe(df_classes, use_container_width=True, hide_index=True)
                else:
                    st.info("Aucune classe trouvée")
            
            with tab2:
                st.subheader("Instances par classe")
                
                # Sélectionner une classe
                if structure['classes']:
                    class_options = {info['label']: uri for uri, info in structure['classes'].items()}
                    selected_class_label = st.selectbox(
                        "Sélectionner une classe:",
                        list(class_options.keys())
                    )
                    
                    selected_class_uri = class_options[selected_class_label]
                    
                    # Afficher les instances
                    query_instances = f"""
                    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                    SELECT ?instance ?label WHERE {{
                        ?instance a <{selected_class_uri}> .
                        OPTIONAL {{ ?instance rdfs:label ?label . }}
                    }}
                    LIMIT 100
                    """
                    
                    try:
                        results = g.query(query_instances)
                        instances = []
                        for row in results:
                            instances.append({
                                'Instance': format_uri(row[0]),
                                'Label': row[1] if row[1] else '-',
                                'URI': row[0]
                            })
                        
                        if instances:
                            st.write(f"**{len(instances)} instances de {selected_class_label}:**")
                            df_instances = pd.DataFrame(instances)
                            st.dataframe(df_instances, use_container_width=True, hide_index=True)
                            
                            # Téléchargement
                            csv = df_instances.to_csv(index=False)
                            st.download_button(
                                "📥 Télécharger instances",
                                csv,
                                f"instances_{selected_class_label}.csv",
                                "text/csv"
                            )
                        else:
                            st.info(f"Aucune instance trouvée pour la classe {selected_class_label}")
                    except Exception as e:
                        st.error(f"Erreur: {e}")
                else:
                    st.info("Aucune classe disponible")
        
        # ===== PAGE: REQUÊTES SPARQL =====
        elif page == "🔍 Requêtes SPARQL":
            st.header("Interface SPARQL")
            
            # Requête par défaut
            if structure['main_prefix'] and structure['main_namespace']:
                default_query = f"""
PREFIX {structure['main_prefix']}: <{structure['main_namespace']}>
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>

SELECT ?s ?p ?o WHERE {{
  ?s ?p ?o .
}}
LIMIT 10
"""
            else:
                default_query = "SELECT * WHERE { ?s ?p ?o } LIMIT 10"
            
            # Éditeur de requête
            query = st.text_area(
                "Votre requête SPARQL:",
                value=default_query,
                height=200
            )
            
            # Options d'exécution
            col_a, col_b = st.columns(2)
            with col_a:
                limit = st.number_input("LIMIT", min_value=1, max_value=1000, value=100)
            with col_b:
                execute = st.button("▶️ Exécuter la requête", type="primary", use_container_width=True)
            
            if execute:
                try:
                    # Ajouter LIMIT si pas déjà présent
                    if "LIMIT" not in query.upper():
                        query = query.rstrip() + f"\nLIMIT {limit}"
                    
                    results = g.query(query)
                    
                    # Traitement des résultats
                    data = []
                    for row in results:
                        row_data = {}
                        for var in results.vars:
                            value = row[var]
                            row_data[str(var)] = format_uri(value) if value is not None else ""
                        data.append(row_data)
                    
                    if data:
                        df = pd.DataFrame(data)
                        
                        # Afficher les résultats
                        st.subheader(f"Résultats ({len(df)} lignes)")
                        st.dataframe(df, use_container_width=True, hide_index=True)
                        
                        # Métriques
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Lignes", len(df))
                        with col2:
                            st.metric("Colonnes", len(df.columns))
                        
                        # Téléchargement CSV
                        csv = df.to_csv(index=False)
                        st.download_button(
                            "📥 Télécharger CSV",
                            csv,
                            "resultats_sparql.csv",
                            "text/csv"
                        )
                    else:
                        st.info("✅ Requête exécutée avec succès, mais aucun résultat trouvé.")
                    
                    # Informations sur l'exécution
                    with st.expander("Informations d'exécution"):
                        st.write(f"**Variables:** {', '.join([str(v) for v in results.vars])}")
                        st.write("**Requête exécutée:**")
                        st.code(query, language="sparql")
                
                except Exception as e:
                    st.error(f"Erreur d'exécution: {str(e)}")
    
    else:
        # ===== SI PAS D'ONTOLOGIE =====
        st.info("""
        ## 📚 Bienvenue dans l'analyseur d'ontologie bibliothèque
        
        Pour commencer:
        1. **Importez une ontologie** via le panneau de gauche
        2. L'application détectera automatiquement sa structure
        3. Explorez les différentes pages pour analyser votre ontologie
        
        Formats supportés: Turtle (.ttl), RDF/XML (.rdf, .owl)
        """)

if __name__ == "__main__":
    main()