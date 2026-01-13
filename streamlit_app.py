import streamlit as st
from rdflib import Graph, URIRef, Namespace, RDF, RDFS, OWL, Literal
import pandas as pd
import matplotlib.pyplot as plt
import os
from pathlib import Path

# Fonction pour charger l'ontologie avec sélection de fichier
@st.cache_resource
def load_ontology(file_path=None):
    g = Graph()
    if file_path:
        try:
            g.parse(file_path, format="turtle")
            st.success(f"Ontologie chargée depuis : {file_path}")
        except Exception as e:
            st.error(f"Erreur lors du chargement du fichier : {e}")
            return None
    return g

def format_uri(uri):
    """Formate une URI pour l'affichage"""
    if isinstance(uri, URIRef):
        uri_str = str(uri)
        if "#" in uri_str:
            return uri_str.split("#")[-1]
        elif "/" in uri_str:
            parts = uri_str.split("/")
            return parts[-1] if parts[-1] else parts[-2]
        return uri_str
    elif isinstance(uri, Literal):
        return str(uri)
    return str(uri)

def main():
    st.title("📚 Système de Validation d'Ontologie Bibliothèque")
    
    # Section pour importer le fichier
    st.sidebar.header("📁 Importation de l'ontologie")
    
    # Option 1: Fichier par défaut
    default_file = "bibliotheque.ttl"
    
    # Option 2: Upload de fichier
    uploaded_file = st.sidebar.file_uploader(
        "Choisir un fichier .ttl", 
        type=['ttl', 'rdf', 'owl'],
        help="Importez votre fichier d'ontologie au format Turtle (.ttl)"
    )
    
    # Déterminer quel fichier utiliser
    file_to_load = None
    
    if uploaded_file is not None:
        # Sauvegarder le fichier uploadé temporairement
        temp_path = f"temp_{uploaded_file.name}"
        with open(temp_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        file_to_load = temp_path
        st.sidebar.success(f"Fichier uploadé : {uploaded_file.name}")
    elif os.path.exists(default_file):
        file_to_load = default_file
        st.sidebar.info(f"Utilisation du fichier par défaut : {default_file}")
    else:
        st.sidebar.warning("Veuillez uploader un fichier .ttl ou placer 'bibliotheque.ttl' dans le même dossier")
    
    # Charger l'ontologie
    if file_to_load:
        g = load_ontology(file_to_load)
        
        if g is None or len(g) == 0:
            st.error("L'ontologie n'a pas pu être chargée ou est vide.")
            return
    else:
        st.info("Veuillez importer un fichier d'ontologie pour continuer.")
        return
    
    # Afficher des informations sur le fichier chargé
    with st.sidebar.expander("📋 Info fichier"):
        st.write(f"**Format détecté :** Turtle")
        st.write(f"**Nombre de triplets :** {len(g)}")
        
        # Détecter les namespaces
        namespaces = dict(g.namespaces())
        if namespaces:
            st.write("**Namespaces détectés :**")
            for prefix, uri in namespaces.items():
                if prefix:  # Éviter les prefixes vides
                    st.write(f"- {prefix}: {uri}")
    
    # Définir les namespaces (essayer de détecter automatiquement)
    namespaces = dict(g.namespaces())
    
    # Chercher le namespace bib s'il existe
    bib_prefix = None
    bib_uri = None
    
    for prefix, uri in namespaces.items():
        if prefix == 'bib':
            bib_prefix = prefix
            bib_uri = uri
            break
        elif 'bibliotheque' in str(uri).lower():
            bib_prefix = prefix if prefix else 'bib'
            bib_uri = uri
    
    # Si pas trouvé, utiliser un namespace par défaut
    if not bib_uri:
        bib_uri = "http://www.semanticweb.org/junior/ontologies/2026/0/bibliotheque#"
        bib_prefix = 'bib'
    
    BIB = Namespace(bib_uri)
    g.bind(bib_prefix, BIB)
    
    st.sidebar.header("Navigation")
    page = st.sidebar.selectbox(
        "Choisir une page",
        ["🏠 Dashboard", "👥 Individus", "✅ Validation", "🔍 Requêtes SPARQL", "📊 Statistiques", "📈 Visualisation"]
    )
    
    if page == "🏠 Dashboard":
        st.header("Tableau de Bord de l'Ontologie")
        
        # Métriques principales
        col1, col2, col3 = st.columns(3)
        
        with col1:
            triple_count = len(g)
            st.metric("Nombre de triplets", triple_count)
        
        with col2:
            query = """
            SELECT (COUNT(DISTINCT ?s) as ?count) WHERE {
                ?s a owl:Class .
            }
            """
            result = g.query(query)
            classes_count = list(result)[0][0]
            st.metric("Classes", int(classes_count))
        
        with col3:
            query = """
            SELECT (COUNT(DISTINCT ?s) as ?count) WHERE {
                ?s ?p ?o .
                FILTER(isLiteral(?o))
            }
            """
            result = g.query(query)
            data_count = list(result)[0][0]
            st.metric("Données littérales", int(data_count))
        
        # Aperçu rapide des classes
        st.subheader("📋 Classes de l'Ontologie")
        query_classes = """
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        SELECT ?class ?label ?comment WHERE {
            ?class a owl:Class .
            OPTIONAL { ?class rdfs:label ?label . }
            OPTIONAL { ?class rdfs:comment ?comment . }
        }
        ORDER BY ?class
        """
        
        results = g.query(query_classes)
        classes_data = []
        for row in results:
            class_name = format_uri(row[0])
            label = format_uri(row[1]) if row[1] else "Pas de label"
            comment = format_uri(row[2]) if row[2] else "Pas de description"
            classes_data.append({
                "Classe": class_name,
                "Label": label,
                "Description": comment
            })
        
        if classes_data:
            df_classes = pd.DataFrame(classes_data)
            st.dataframe(df_classes, use_container_width=True)
        else:
            st.info("Aucune classe trouvée dans l'ontologie")
    
    elif page == "👥 Individus":
        st.header("👥 Gestion des Individus (Instances)")
        
        # Sélectionner une classe pour voir ses instances
        st.subheader("Filtrer par classe")
        
        # Récupérer toutes les classes
        query_all_classes = """
        SELECT DISTINCT ?class WHERE {
            ?class a owl:Class .
        }
        ORDER BY ?class
        """
        
        classes_result = g.query(query_all_classes)
        classes_list = [("Toutes les classes", None)] + [(format_uri(row[0]), row[0]) for row in classes_result]
        
        selected_class_name = st.selectbox(
            "Choisir une classe:",
            options=[c[0] for c in classes_list],
            index=0
        )
        
        selected_class = next(c[1] for c in classes_list if c[0] == selected_class_name)
        
        if selected_class:
            # Construire la requête SPARQL
            if selected_class_name == "Toutes les classes":
                query_instances = """
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                SELECT ?instance ?class ?label WHERE {
                    ?instance a ?class .
                    FILTER(?class != owl:Class && ?class != rdfs:Class)
                    OPTIONAL { ?instance rdfs:label ?label . }
                }
                ORDER BY ?class ?instance
                """
            else:
                query_instances = f"""
                PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
                PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
                SELECT ?instance ?label WHERE {{
                    ?instance a <{selected_class}> .
                    OPTIONAL {{ ?instance rdfs:label ?label . }}
                }}
                ORDER BY ?instance
                """
            
            # Exécuter la requête
            results = g.query(query_instances)
            instances_data = []
            
            for row in results:
                if selected_class_name == "Toutes les classes":
                    instance_name = format_uri(row[0])
                    class_name = format_uri(row[1])
                    label = format_uri(row[2]) if row[2] else "Sans label"
                    instances_data.append({
                        "Instance": instance_name,
                        "Classe": class_name,
                        "Label": label
                    })
                else:
                    instance_name = format_uri(row[0])
                    label = format_uri(row[1]) if row[1] else "Sans label"
                    instances_data.append({
                        "Instance": instance_name,
                        "Label": label
                    })
            
            if instances_data:
                st.write(f"**{len(instances_data)} instances trouvées**")
                df_instances = pd.DataFrame(instances_data)
                st.dataframe(df_instances, use_container_width=True)
                
                # Option de téléchargement
                csv = df_instances.to_csv(index=False)
                st.download_button(
                    label="📥 Télécharger les données (CSV)",
                    data=csv,
                    file_name=f"instances_{selected_class_name.lower().replace(' ', '_')}.csv",
                    mime="text/csv"
                )
            else:
                st.info(f"Aucune instance trouvée pour la classe {selected_class_name}")
    
    elif page == "✅ Validation":
        st.header("✅ Validation de l'Ontologie")
        
        # Note: Les préfixes dans les requêtes seront adaptés automatiquement
        st.info(f"Utilisation du namespace : {bib_prefix}: {bib_uri}")
        
        # Validation des emprunts
        st.subheader("📖 Validation des Emprunts")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("Vérifier cohérence emprunts"):
                query = f"""
                PREFIX {bib_prefix}: <{bib_uri}>
                SELECT ?emprunt ?membre ?document WHERE {{
                    ?emprunt a {bib_prefix}:Emprunt .
                    ?emprunt {bib_prefix}:effectuePar ?membre .
                    ?emprunt {bib_prefix}:porteSur ?document .
                    OPTIONAL {{ ?membre a {bib_prefix}:Membre . }}
                    OPTIONAL {{ ?document a {bib_prefix}:Document . }}
                    FILTER(!BOUND(?membre) || !BOUND(?document))
                }}
                """
                results = g.query(query)
                issues = list(results)
                if issues:
                    st.error(f"❌ Problèmes trouvés: {len(issues)}")
                    for issue in issues:
                        st.write(f"- Emprunt {format_uri(issue[0])}: Membre ou Document manquant")
                else:
                    st.success("✅ Tous les emprunts sont cohérents")
        
        with col2:
            if st.button("Vérifier dates emprunts"):
                query = f"""
                PREFIX {bib_prefix}: <{bib_uri}>
                PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
                SELECT ?emprunt ?dateDebut ?dateFin WHERE {{
                    ?emprunt a {bib_prefix}:Emprunt .
                    ?emprunt {bib_prefix}:dateDebut ?dateDebut .
                    ?emprunt {bib_prefix}:dateFin ?dateFin .
                    FILTER(xsd:dateTime(?dateFin) < xsd:dateTime(?dateDebut))
                }}
                """
                results = g.query(query)
                issues = list(results)
                if issues:
                    st.error(f"❌ Dates incohérentes: {len(issues)}")
                    for issue in issues:
                        st.write(f"- {format_uri(issue[0])}: {issue[1]} → {issue[2]}")
                else:
                    st.success("✅ Toutes les dates sont cohérentes")
        
        with col3:
            if st.button("Emprunts en retard"):
                query = f"""
                PREFIX {bib_prefix}: <{bib_uri}>
                PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
                SELECT ?emprunt ?membre ?document ?dateFin WHERE {{
                    ?emprunt a {bib_prefix}:Emprunt .
                    ?emprunt {bib_prefix}:effectuePar ?membre .
                    ?emprunt {bib_prefix}:porteSur ?document .
                    ?emprunt {bib_prefix}:dateFin ?dateFin .
                    FILTER(xsd:dateTime(?dateFin) < xsd:dateTime(NOW()))
                }}
                """
                results = g.query(query)
                late_loans = list(results)
                if late_loans:
                    st.warning(f"⚠️ Emprunts en retard: {len(late_loans)}")
                    for loan in late_loans:
                        st.write(f"- {format_uri(loan[1])} → {format_uri(loan[2])} (retour le {loan[3]})")
                else:
                    st.success("✅ Aucun emprunt en retard")
    
    elif page == "🔍 Requêtes SPARQL":
        st.header("🔍 Interface SPARQL Avancée")
        
        # Préfixes par défaut basés sur votre ontologie
        default_prefixes = f"""PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
PREFIX {bib_prefix}: <{bib_uri}>"""
        
        # Zone pour les préfixes personnalisés
        with st.expander("⚙️ Préfixes SPARQL", expanded=True):
            custom_prefixes = st.text_area(
                "Définir vos préfixes:",
                value=default_prefixes,
                height=150,
                help="Modifiez ou ajoutez des préfixes selon vos besoins"
            )
        
        # Zone de requête principale
        default_query = f"""SELECT ?livre ?titre
WHERE {{
  ?livre rdf:type {bib_prefix}:Livre .
  ?livre {bib_prefix}:titre ?titre .
}}"""
        
        # Combiner préfixes et requête
        full_query = custom_prefixes + "\n\n" + default_query
        
        query = st.text_area(
            "Éditez votre requête SPARQL complète:",
            value=full_query,
            height=250,
            key="sparql_editor"
        )
        
        # Options d'exécution
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            execute = st.button("▶️ Exécuter", type="primary", use_container_width=True)
        
        with col2:
            limit = st.number_input("Limite", min_value=10, max_value=1000, value=100, key="limit")
        
        with col3:
            output_format = st.selectbox(
                "Format",
                ["Tableau", "Liste", "JSON", "Graphique"]
            )
        
        if execute and query:
            try:
                # Ajouter la limite si nécessaire
                if "LIMIT" not in query.upper() and limit != 100:
                    query_lines = query.strip().split('\n')
                    if query_lines[-1].strip().upper().startswith('ORDER BY'):
                        query_lines.append(f"LIMIT {limit}")
                    else:
                        query_lines[-1] = query_lines[-1].rstrip() + f"\nLIMIT {limit}"
                    query = '\n'.join(query_lines)
                
                # Exécuter la requête
                results = g.query(query)
                
                # Traiter les résultats selon le format choisi
                if output_format == "Tableau":
                    data = []
                    for row in results:
                        row_data = {}
                        for i, var in enumerate(results.vars):
                            value = row[i]
                            if value is not None:
                                if isinstance(value, URIRef):
                                    row_data[str(var)] = format_uri(value)
                                elif isinstance(value, Literal):
                                    row_data[str(var)] = str(value)
                                else:
                                    row_data[str(var)] = str(value)
                            else:
                                row_data[str(var)] = ""
                        data.append(row_data)
                    
                    if data:
                        df = pd.DataFrame(data)
                        
                        # Afficher les résultats
                        st.subheader(f"📊 Résultats ({len(df)} lignes)")
                        st.dataframe(df, use_container_width=True)
                        
                        # Métriques
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric("Lignes", len(df))
                        with col2:
                            st.metric("Colonnes", len(df.columns))
                        with col3:
                            unique_count = sum(df.nunique())
                            st.metric("Valeurs uniques", unique_count)
                        
                        # Options de téléchargement
                        col_dl1, col_dl2 = st.columns(2)
                        with col_dl1:
                            csv = df.to_csv(index=False, sep=';')
                            st.download_button(
                                label="📥 Télécharger CSV",
                                data=csv,
                                file_name="resultats_sparql.csv",
                                mime="text/csv"
                            )
                        
                        
                    else:
                        st.info("✅ Requête exécutée avec succès, mais aucun résultat trouvé.")
                
                elif output_format == "Liste":
                    st.subheader("📝 Liste des résultats")
                    for i, row in enumerate(results, 1):
                        row_items = []
                        for j, val in enumerate(row):
                            var_name = str(results.vars[j])
                            formatted_val = format_uri(val) if val is not None else "NULL"
                            row_items.append(f"{var_name}: {formatted_val}")
                        st.write(f"{i}. " + " | ".join(row_items))
                
                elif output_format == "JSON":
                    import json
                    data = []
                    for row in results:
                        row_dict = {}
                        for var, val in zip(results.vars, row):
                            if val is not None:
                                row_dict[str(var)] = format_uri(val)
                            else:
                                row_dict[str(var)] = None
                        data.append(row_dict)
                    
                    st.json(data)
                    
                    json_str = json.dumps(data, indent=2, ensure_ascii=False)
                    st.download_button(
                        label="📥 Télécharger JSON",
                        data=json_str,
                        file_name="resultats_sparql.json",
                        mime="application/json"
                    )
                
                elif output_format == "Graphique":
                    # Essayer de créer un graphique à partir des résultats
                    data = []
                    for row in results:
                        row_data = {}
                        for i, var in enumerate(results.vars):
                            value = row[i]
                            if value is not None:
                                row_data[str(var)] = format_uri(value)
                            else:
                                row_data[str(var)] = ""
                        data.append(row_data)
                    
                    if data and len(data) > 0:
                        df = pd.DataFrame(data)
                        
                        # Essayer différents types de visualisation
                        if len(df.columns) >= 2:
                            st.subheader("📈 Visualisation des résultats")
                            
                            # Détecter le type de données pour la visualisation
                            col1_name = df.columns[0]
                            col2_name = df.columns[1] if len(df.columns) > 1 else None
                            
                            # Vérifier si la deuxième colonne est numérique
                            try:
                                if col2_name:
                                    df[col2_name] = pd.to_numeric(df[col2_name], errors='ignore')
                                    
                                    if pd.api.types.is_numeric_dtype(df[col2_name]):
                                        # Graphique à barres pour données numériques
                                        fig, ax = plt.subplots(figsize=(10, 6))
                                        top_data = df.nlargest(10, col2_name)
                                        bars = ax.barh(top_data[col1_name].astype(str), top_data[col2_name])
                                        ax.set_xlabel(col2_name)
                                        ax.set_title(f"Top 10 - {col2_name} par {col1_name}")
                                        
                                        # Ajouter les valeurs sur les barres
                                        for bar in bars:
                                            width = bar.get_width()
                                            ax.text(width + 0.1, bar.get_y() + bar.get_height()/2,
                                                   f'{width:.1f}', va='center')
                                        
                                        plt.tight_layout()
                                        st.pyplot(fig)
                                    else:
                                        # Diagramme en barres simple pour données catégorielles
                                        value_counts = df[col1_name].value_counts().head(10)
                                        fig, ax = plt.subplots(figsize=(10, 6))
                                        bars = ax.bar(range(len(value_counts)), value_counts.values)
                                        ax.set_xticks(range(len(value_counts)))
                                        ax.set_xticklabels(value_counts.index, rotation=45, ha='right')
                                        ax.set_ylabel("Nombre")
                                        ax.set_title(f"Distribution de {col1_name}")
                                        
                                        for bar in bars:
                                            height = bar.get_height()
                                            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                                                   f'{int(height)}', ha='center', va='bottom')
                                        
                                        plt.tight_layout()
                                        st.pyplot(fig)
                            except:
                                # Si la visualisation échoue, afficher un message
                                st.info("Les données ne sont pas adaptées à une visualisation automatique.")
                                st.dataframe(df.head(20))
                        else:
                            st.dataframe(df)
                
                # Afficher des informations sur l'exécution
                with st.expander("🔍 Informations d'exécution"):
                    st.write(f"**Nombre de variables:** {len(results.vars)}")
                    st.write(f"**Variables:** {', '.join([str(v) for v in results.vars])}")
                    st.write(f"**Temps d'exécution:** Instantané (mémoire)")
                    
                    # Afficher la requête formatée
                    st.write("**Requête exécutée:**")
                    st.code(query, language="sparql")
                    
            except Exception as e:
                st.error(f"❌ Erreur d'exécution SPARQL: {str(e)}")
                
                # Aide pour le débogage
                with st.expander("🛠️ Aide au débogage"):
                    st.write("Vérifiez:")
                    st.write("1. ✅ La syntaxe SPARQL est correcte")
                    st.write("2. ✅ Les préfixes sont bien définis")
                    st.write("3. ✅ Les noms de classes/propriétés existent dans l'ontologie")
                    st.write("4. ✅ Pas de faute de frappe dans les noms")
                    
                    # Afficher un exemple correct
                    st.write("**Exemple de requête valide:**")
                    st.code(f"""PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX {bib_prefix}: <{bib_uri}>

SELECT ?s ?p ?o
WHERE {{
  ?s ?p ?o .
}}
LIMIT 10""", language="sparql")
    
    elif page == "📊 Statistiques":
        st.header("📊 Statistiques Détaillées")
        
        # Calculer les statistiques
        queries = {
            "Triplets totaux": """
            SELECT (COUNT(*) as ?count) WHERE {
                ?s ?p ?o .
            }
            """,
            "Sujets uniques": """
            SELECT (COUNT(DISTINCT ?s) as ?count) WHERE {
                ?s ?p ?o .
            }
            """,
            "Propriétés uniques": """
            SELECT (COUNT(DISTINCT ?p) as ?count) WHERE {
                ?s ?p ?o .
            }
            """,
            "Objets uniques": """
            SELECT (COUNT(DISTINCT ?o) as ?count) WHERE {
                ?s ?p ?o .
            }
            """,
            "Données littérales": """
            SELECT (COUNT(*) as ?count) WHERE {
                ?s ?p ?o .
                FILTER(isLiteral(?o))
            }
            """,
            "Relations (non-littéral)": """
            SELECT (COUNT(*) as ?count) WHERE {
                ?s ?p ?o .
                FILTER(!isLiteral(?o))
            }
            """
        }
        
        stats = {}
        for name, query in queries.items():
            try:
                result = g.query(query)
                stats[name] = int(list(result)[0][0])
            except:
                stats[name] = 0
        
        # Afficher les métriques
        cols = st.columns(3)
        stat_items = list(stats.items())
        
        for i, (name, value) in enumerate(stat_items):
            with cols[i % 3]:
                st.metric(name, value)
        
        # Graphique des statistiques générales
        st.subheader("📈 Répartition des données")
        fig, ax = plt.subplots(figsize=(10, 5))
        
        bars = ax.bar(stats.keys(), stats.values())
        ax.set_ylabel("Nombre")
        ax.set_title("Statistiques générales")
        ax.tick_params(axis='x', rotation=45)
        
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                   f'{int(height)}', ha='center', va='bottom')
        
        plt.tight_layout()
        st.pyplot(fig)
        
        # Analyse des patterns
        st.subheader("🔍 Patterns détectés")
        
        query_patterns = """
        SELECT ?type (COUNT(?s) as ?count) WHERE {
            ?s a ?type .
        }
        GROUP BY ?type
        ORDER BY DESC(?count)
        LIMIT 10
        """
        
        results = g.query(query_patterns)
        patterns = []
        for row in results:
            patterns.append({
                "Type": format_uri(row[0]),
                "Nombre": int(row[1])
            })
        
        if patterns:
            df_patterns = pd.DataFrame(patterns)
            st.dataframe(df_patterns, use_container_width=True)
    
    elif page == "📈 Visualisation":
        st.header("📈 Visualisations du graphe RDF")
        
        # Visualisation simple du graphe
        st.subheader("🕸️ Vue d'ensemble du graphe")
        
        # Échantillon du graphe pour visualisation
        query_sample = """
        SELECT ?s ?p ?o WHERE {
            ?s ?p ?o .
            FILTER(!isLiteral(?o) || (isLiteral(?o) && STRLEN(STR(?o)) < 50))
        }
        LIMIT 50
        """
        
        results = g.query(query_sample)
        
        # Créer une visualisation textuelle
        st.write("**Échantillon de 50 triplets RDF:**")
        
        sample_data = []
        for i, row in enumerate(results, 1):
            sample_data.append({
                "N°": i,
                "Sujet": format_uri(row[0]),
                "Propriété": format_uri(row[1]),
                "Objet": format_uri(row[2])
            })
        
        if sample_data:
            df_sample = pd.DataFrame(sample_data)
            st.dataframe(df_sample, use_container_width=True)
        
        # Nettoyer le fichier temporaire si nécessaire
        if uploaded_file and os.path.exists(f"temp_{uploaded_file.name}"):
            os.remove(f"temp_{uploaded_file.name}")

if __name__ == "__main__":
    main()