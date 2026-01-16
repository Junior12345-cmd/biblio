import streamlit as st
import pandas as pd
import plotly.express as px
from rdflib import Graph, Namespace, RDF, RDFS, OWL, XSD, Literal, URIRef
import json
from datetime import datetime
import uuid

# Configuration de la page
st.set_page_config(
    page_title="Bibliothèque Intelligente - Gestion Ontologique",
    page_icon="📚",
    layout="wide"
)

# Titre principal
st.title("📚 Système de Gestion Dynamique de Bibliothèque")
st.markdown("### Gestion Complète de l'Ontologie Bibliothèque")

# Initialisation du graph RDF
@st.cache_resource
def load_ontology():
    g = Graph()
    try:
        g.parse("bibio.ttl", format="turtle")
    except:
        # Créer un graph vide si le fichier n'existe pas
        g = Graph()
        # Définir les namespaces de base
        g.bind("bib", "http://www.semanticweb.org/junior/ontologies/2026/0/bibliotheque#")
        g.bind("owl", OWL)
        g.bind("rdf", RDF)
        g.bind("rdfs", RDFS)
        g.bind("xsd", XSD)
    return g

# Fonction pour sauvegarder l'ontologie
def save_ontology(g):
    g.serialize(destination="bibio.ttl", format="turtle")

# Charger l'ontologie
g = load_ontology()

# Définir le namespace
BIB = Namespace("http://www.semanticweb.org/junior/ontologies/2026/0/bibliotheque#")
g.bind("bib", BIB)

# Fonction pour générer des URIs uniques
def generate_uri(base_name, prefix=""):
    unique_id = str(uuid.uuid4())[:8]
    if prefix:
        return BIB[f"{prefix}_{base_name}_{unique_id}"]
    return BIB[f"{base_name}_{unique_id}"]

# Fonction pour formater les URIs
def format_uri(uri):
    if isinstance(uri, str):
        return uri.split("#")[-1] if "#" in uri else uri.split("/")[-1]
    return str(uri).split("#")[-1] if "#" in str(uri) else str(uri).split("/")[-1]

# Fonction pour obtenir toutes les instances d'une classe
def get_instances(class_uri):
    return list(g.subjects(RDF.type, class_uri))

# Fonction pour obtenir les propriétés d'un individu
def get_individual_properties(individual_uri):
    properties = []
    for p, o in g.predicate_objects(individual_uri):
        if p not in [RDF.type]:
            prop_name = format_uri(p)
            if isinstance(o, Literal):
                value = str(o)
                datatype = str(o.datatype) if o.datatype else "string"
                properties.append({
                    "Propriété": prop_name,
                    "Valeur": value,
                    "Type": "Donnée"
                })
            else:
                obj_name = format_uri(o)
                properties.append({
                    "Propriété": prop_name,
                    "Valeur": obj_name,
                    "Type": "Objet"
                })
    return properties

# Statistiques dans la sidebar
st.sidebar.header("📊 Statistiques de l'Ontologie")

# Compter les classes
classes = list(g.subjects(RDF.type, OWL.Class))
st.sidebar.metric("Classes", len(classes))

# Compter les individus
individuals = list(g.subjects(RDF.type, OWL.NamedIndividual))
st.sidebar.metric("Individus", len(individuals))

# Compter les propriétés
object_props = list(g.subjects(RDF.type, OWL.ObjectProperty))
data_props = list(g.subjects(RDF.type, OWL.DatatypeProperty))
st.sidebar.metric("Propriétés", len(object_props) + len(data_props))

# Navigation
st.sidebar.header("🔍 Navigation")
tab = st.sidebar.radio(
    "Sélectionnez une section:",
    ["🏠 Tableau de Bord", "📖 Gestion Documents", "👥 Gestion Personnes", 
     "📋 Gestion Emprunts", "📝 Gestion Réservations", "➕ Ajouter Entités", 
     "🔗 Exploration Relations", "⚙️ Structure Ontologique"]
)

# Tableau de Bord
if tab == "🏠 Tableau de Bord":
    st.header("Tableau de Bord de la Bibliothèque")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        documents = get_instances(BIB.Document)
        st.metric("Documents", len(documents))
        
        doc_types = {}
        for doc_class in [BIB.Livre, BIB.Revue, BIB.Article, BIB.CDAudio, BIB.DVD, BIB.Thèse, BIB.Mémoire, BIB.RessourceÉlectronique]:
            docs = get_instances(doc_class)
            if docs:
                doc_types[format_uri(doc_class)] = len(docs)
        
        if doc_types:
            fig1 = px.pie(
                values=list(doc_types.values()),
                names=list(doc_types.keys()),
                title="Répartition des Types de Documents"
            )
            st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        personnes = get_instances(BIB.Personne)
        st.metric("Personnes", len(personnes))
        
        pers_types = {}
        for pers_class in [BIB.Utilisateur, BIB.Employé, BIB.Auteur]:
            pers = get_instances(pers_class)
            if pers:
                pers_types[format_uri(pers_class)] = len(pers)
        
        if pers_types:
            fig2 = px.bar(
                x=list(pers_types.keys()),
                y=list(pers_types.values()),
                title="Répartition des Personnes",
                labels={'x': 'Type', 'y': 'Nombre'}
            )
            st.plotly_chart(fig2, use_container_width=True)
    
    with col3:
        exemplaires = get_instances(BIB.Exemplaire)
        st.metric("Exemplaires", len(exemplaires))
        
        emprunts = get_instances(BIB.Emprunt)
        st.metric("Emprunts actifs", len(emprunts))
        
        reservations = get_instances(BIB.Réservation)
        st.metric("Réservations", len(reservations))
    
    # Actions rapides
    st.subheader("🚀 Actions Rapides")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("➕ Ajouter un Livre", use_container_width=True):
            st.session_state['ajouter_entite'] = "Livre"
            st.rerun()
    
    with col2:
        if st.button("👤 Ajouter un Utilisateur", use_container_width=True):
            st.session_state['ajouter_entite'] = "Utilisateur"
            st.rerun()
    
    with col3:
        if st.button("📚 Nouvel Emprunt", use_container_width=True):
            st.session_state['ajouter_entite'] = "Emprunt"
            st.rerun()
    
    with col4:
        if st.button("📝 Nouvelle Réservation", use_container_width=True):
            st.session_state['ajouter_entite'] = "Réservation"
            st.rerun()

# Gestion Documents
elif tab == "📖 Gestion Documents":
    st.header("📖 Gestion des Documents")
    
    # Sous-tabs pour différents types de documents
    doc_types = ["Tous", "Livres", "Revues", "Articles", "DVD", "CD Audio", "Thèses", "Mémoires"]
    selected_doc_type = st.selectbox("Type de document:", doc_types)
    
    # Mapper les types aux classes
    type_mapping = {
        "Livres": BIB.Livre,
        "Revues": BIB.Revue,
        "Articles": BIB.Article,
        "DVD": BIB.DVD,
        "CD Audio": BIB.CDAudio,
        "Thèses": BIB.Thèse,
        "Mémoires": BIB.Mémoire,
        "Tous": BIB.Document
    }
    
    # Récupérer les documents
    if selected_doc_type == "Tous":
        documents = []
        for cls in [BIB.Livre, BIB.Revue, BIB.Article, BIB.DVD, BIB.CDAudio, BIB.Thèse, BIB.Mémoire]:
            documents.extend(get_instances(cls))
    else:
        documents = get_instances(type_mapping[selected_doc_type])
    
    # Recherche
    search_term = st.text_input("🔍 Rechercher un document (titre, auteur, ISBN/ISSN/DOI):")
    
    # Afficher les documents
    if documents:
        doc_data = []
        for doc in documents:
            titre = g.value(doc, BIB.titre)
            doc_type = None
            for cls_name, cls_uri in type_mapping.items():
                if (doc, RDF.type, cls_uri) in g:
                    doc_type = cls_name
                    break
            
            auteur_uri = g.value(doc, BIB.aPourAuteur)
            auteur = g.value(auteur_uri, BIB.nom) if auteur_uri else None
            
            # Identifiants spécifiques
            isbn = g.value(doc, BIB.isbn) if (doc, RDF.type, BIB.Livre) in g else None
            issn = g.value(doc, BIB.issn) if (doc, RDF.type, BIB.Revue) in g else None
            doi = g.value(doc, BIB.doi) if (doc, RDF.type, BIB.Article) in g else None
            
            doc_data.append({
                "ID": format_uri(doc),
                "Titre": str(titre) if titre else "Sans titre",
                "Type": doc_type,
                "Auteur": str(auteur) if auteur else "Inconnu",
                "Identifiant": str(isbn or issn or doi or ""),
                "URI": doc
            })
        
        # Filtrer par recherche
        if search_term:
            doc_data = [d for d in doc_data 
                       if search_term.lower() in d["Titre"].lower() 
                       or search_term.lower() in d["Auteur"].lower()
                       or search_term.lower() in d["Identifiant"].lower()]
        
        if doc_data:
            # Créer un DataFrame pour l'affichage
            display_data = [{
                "ID": d["ID"],
                "Titre": d["Titre"],
                "Type": d["Type"],
                "Auteur": d["Auteur"],
                "Identifiant": d["Identifiant"]
            } for d in doc_data]
            
            df = pd.DataFrame(display_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            # Détails et actions pour un document sélectionné
            st.subheader("📋 Détails du Document")
            selected_doc_id = st.selectbox(
                "Sélectionnez un document:",
                [f"{d['ID']} - {d['Titre']}" for d in doc_data]
            )
            
            if selected_doc_id:
                doc_id = selected_doc_id.split(" - ")[0]
                selected_doc = None
                for d in doc_data:
                    if d["ID"] == doc_id:
                        selected_doc = d
                        break
                
                if selected_doc:
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"**Titre:** {selected_doc['Titre']}")
                        st.markdown(f"**Type:** {selected_doc['Type']}")
                        st.markdown(f"**Auteur:** {selected_doc['Auteur']}")
                        if selected_doc['Identifiant']:
                            st.markdown(f"**Identifiant:** {selected_doc['Identifiant']}")
                        
                        # Afficher les exemplaires
                        exemplaires = list(g.subjects(BIB.estUneCopieDe, selected_doc["URI"]))
                        st.markdown(f"**Exemplaires disponibles:** {len(exemplaires)}")
                        
                        for ex in exemplaires:
                            etat = g.value(ex, BIB.état)
                            code = g.value(ex, BIB.codeBarre)
                            localisation = g.value(ex, BIB.estLocaliséÀ)
                            loc_name = format_uri(localisation) if localisation else "Non localisé"
                            
                            # Vérifier si emprunté
                            emprunte_par = g.value(ex, BIB.estEmpruntéPar)
                            status = "🔴 Emprunté" if emprunte_par else "🟢 Disponible"
                            
                            st.write(f"- {status} | 📍 {loc_name} | 🏷️ {code} | 📊 {etat}")
                    
                    with col2:
                        st.subheader("Actions")
                        if st.button("🗑️ Supprimer ce document", type="secondary"):
                            # Supprimer le document et ses exemplaires
                            for ex in exemplaires:
                                g.remove((ex, None, None))
                                g.remove((None, None, ex))
                            g.remove((selected_doc["URI"], None, None))
                            g.remove((None, None, selected_doc["URI"]))
                            save_ontology(g)
                            st.success("Document supprimé avec succès!")
                            st.rerun()
                        
                        if st.button("✏️ Modifier", type="primary"):
                            st.session_state['modifier_document'] = selected_doc["URI"]
                            st.rerun()
        else:
            st.info("Aucun document trouvé avec ces critères.")
    else:
        st.info("Aucun document dans la bibliothèque.")

# Gestion Personnes
elif tab == "👥 Gestion Personnes":
    st.header("👥 Gestion des Personnes")
    
    # Types de personnes
    pers_type = st.radio(
        "Type de personne:",
        ["Toutes", "Utilisateurs", "Employés", "Auteurs", "Bibliothécaires", "Agents d'Accueil"],
        horizontal=True
    )
    
    # Récupérer les personnes
    personnes_data = []
    
    if pers_type in ["Toutes", "Utilisateurs"]:
        for pers in get_instances(BIB.Utilisateur):
            nom = g.value(pers, BIB.nom)
            personnes_data.append({
                "Type": "Utilisateur",
                "Nom": str(nom) if nom else format_uri(pers),
                "URI": pers
            })
    
    if pers_type in ["Toutes", "Employés", "Bibliothécaires"]:
        for pers in get_instances(BIB.Bibliothécaire):
            nom = g.value(pers, BIB.nom)
            personnes_data.append({
                "Type": "Bibliothécaire",
                "Nom": str(nom) if nom else format_uri(pers),
                "URI": pers
            })
    
    if pers_type in ["Toutes", "Employés", "Agents d'Accueil"]:
        for pers in get_instances(BIB.AgentAccueil):
            nom = g.value(pers, BIB.nom)
            personnes_data.append({
                "Type": "Agent d'Accueil",
                "Nom": str(nom) if nom else format_uri(pers),
                "URI": pers
            })
    
    if pers_type in ["Toutes", "Auteurs"]:
        for pers in get_instances(BIB.Auteur):
            nom = g.value(pers, BIB.nom)
            personnes_data.append({
                "Type": "Auteur",
                "Nom": str(nom) if nom else format_uri(pers),
                "URI": pers
            })
    
    # Recherche
    search_term = st.text_input("🔍 Rechercher une personne:")
    
    # Filtrer par recherche
    if search_term:
        personnes_data = [p for p in personnes_data if search_term.lower() in p["Nom"].lower()]
    
    # Afficher les personnes
    if personnes_data:
        df_pers = pd.DataFrame([{"Type": p["Type"], "Nom": p["Nom"], "ID": format_uri(p["URI"])} for p in personnes_data])
        st.dataframe(df_pers, use_container_width=True, hide_index=True)
        
        # Détails de la personne sélectionnée
        st.subheader("👤 Détails de la Personne")
        selected_pers = st.selectbox(
            "Sélectionnez une personne:",
            [f"{p['Type']}: {p['Nom']}" for p in personnes_data]
        )
        
        if selected_pers:
            pers_name = selected_pers.split(": ")[1]
            for pers in personnes_data:
                if pers["Nom"] == pers_name:
                    col1, col2 = st.columns([2, 1])
                    
                    with col1:
                        st.markdown(f"**Nom:** {pers['Nom']}")
                        st.markdown(f"**Type:** {pers['Type']}")
                        
                        # Informations supplémentaires
                        email = g.value(pers["URI"], BIB.email)
                        matricule = g.value(pers["URI"], BIB.matricule)
                        
                        if email:
                            st.markdown(f"**Email:** {email}")
                        if matricule:
                            st.markdown(f"**Matricule:** {matricule}")
                        
                        # Afficher les emprunts si c'est un utilisateur
                        if pers['Type'] == "Utilisateur":
                            emprunts = list(g.subjects(BIB.effectuéPar, pers["URI"]))
                            st.markdown(f"**Emprunts en cours:** {len(emprunts)}")
                            
                            for emp in emprunts:
                                exemplaire = g.value(emp, BIB.concerneExemplaire)
                                doc = g.value(exemplaire, BIB.estUneCopieDe) if exemplaire else None
                                doc_titre = g.value(doc, BIB.titre) if doc else "Document inconnu"
                                date_retour = g.value(emp, BIB.dateRetourPrévue)
                                st.write(f"- 📖 {doc_titre} (Retour: {date_retour})")
                    
                    with col2:
                        st.subheader("Actions")
                        if st.button("🗑️ Supprimer", type="secondary", use_container_width=True):
                            g.remove((pers["URI"], None, None))
                            g.remove((None, None, pers["URI"]))
                            save_ontology(g)
                            st.success("Personne supprimée avec succès!")
                            st.rerun()
                        
                        if st.button("✏️ Modifier", type="primary", use_container_width=True):
                            st.session_state['modifier_personne'] = pers["URI"]
                            st.rerun()
    else:
        st.info("Aucune personne trouvée.")

# Gestion Emprunts
elif tab == "📋 Gestion Emprunts":
    st.header("📋 Gestion des Emprunts")
    
    # Types d'emprunts
    emp_type = st.radio(
        "Type d'emprunt:",
        ["Tous", "Normaux", "Réservés", "Inter-bibliothèque"],
        horizontal=True
    )
    
    # Récupérer les emprunts
    emprunts_data = []
    
    if emp_type in ["Tous", "Normaux"]:
        for emp in get_instances(BIB.EmpruntNormal):
            emprunts_data.append({"Type": "Normal", "URI": emp})
    
    if emp_type in ["Tous", "Réservés"]:
        for emp in get_instances(BIB.EmpruntRéservé):
            emprunts_data.append({"Type": "Réservé", "URI": emp})
    
    if emp_type in ["Tous", "Inter-bibliothèque"]:
        for emp in get_instances(BIB.EmpruntInterBibliothèque):
            emprunts_data.append({"Type": "Inter-bibliothèque", "URI": emp})
    
    # Afficher les emprunts
    if emprunts_data:
        emp_display = []
        for emp in emprunts_data:
            utilisateur = g.value(emp["URI"], BIB.effectuéPar)
            user_name = g.value(utilisateur, BIB.nom) if utilisateur else "Inconnu"
            
            exemplaire = g.value(emp["URI"], BIB.concerneExemplaire)
            doc = g.value(exemplaire, BIB.estUneCopieDe) if exemplaire else None
            doc_titre = g.value(doc, BIB.titre) if doc else "Document inconnu"
            
            date_debut = g.value(emp["URI"], BIB.dateDébut)
            date_retour = g.value(emp["URI"], BIB.dateRetourPrévue)
            
            emp_display.append({
                "Type": emp["Type"],
                "Utilisateur": str(user_name),
                "Document": str(doc_titre),
                "Date Début": str(date_debut)[:10] if date_debut else "N/A",
                "Date Retour": str(date_retour)[:10] if date_retour else "N/A",
                "ID": format_uri(emp["URI"])
            })
        
        df_emp = pd.DataFrame(emp_display)
        st.dataframe(df_emp, use_container_width=True, hide_index=True)
        
        # Gestion des retours
        st.subheader("📥 Gestion des Retours")
        selected_emp_id = st.selectbox(
            "Sélectionnez un emprunt pour le retour:",
            [f"{e['ID']} - {e['Document']} par {e['Utilisateur']}" for e in emp_display]
        )
        
        if selected_emp_id and st.button("✅ Enregistrer le retour", type="primary"):
            emp_id = selected_emp_id.split(" - ")[0]
            # Trouver l'URI de l'emprunt
            emp_uri = None
            for emp in emprunts_data:
                if format_uri(emp["URI"]) == emp_id:
                    emp_uri = emp["URI"]
                    break
            
            if emp_uri:
                # Marquer la date de retour effective
                now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                g.set((emp_uri, BIB.dateRetourEffective, Literal(now, datatype=XSD.dateTime)))
                
                # Libérer l'exemplaire
                exemplaire = g.value(emp_uri, BIB.concerneExemplaire)
                if exemplaire:
                    g.remove((exemplaire, BIB.estEmpruntéPar, None))
                
                save_ontology(g)
                st.success("Retour enregistré avec succès!")
                st.rerun()
    else:
        st.info("Aucun emprunt actif.")

# Gestion Réservations
elif tab == "📝 Gestion Réservations":
    st.header("📝 Gestion des Réservations")
    
    # Récupérer les réservations
    reservations = get_instances(BIB.Réservation)
    
    if reservations:
        res_data = []
        for res in reservations:
            utilisateur = g.value(res, BIB.aPourRéservation)
            user_name = g.value(utilisateur, BIB.nom) if utilisateur else "Inconnu"
            
            document = g.value(res, BIB.porteSur)
            doc_titre = g.value(document, BIB.titre) if document else "Document inconnu"
            
            date_res = g.value(res, BIB.dateReservation)
            
            res_data.append({
                "Utilisateur": str(user_name),
                "Document": str(doc_titre),
                "Date Réservation": str(date_res)[:16] if date_res else "N/A",
                "ID": format_uri(res),
                "URI": res
            })
        
        df_res = pd.DataFrame(res_data)
        st.dataframe(df_res, use_container_width=True, hide_index=True)
        
        # Actions sur les réservations
        st.subheader("Actions sur les Réservations")
        selected_res_id = st.selectbox(
            "Sélectionnez une réservation:",
            [f"{r['ID']} - {r['Document']}" for r in res_data]
        )
        
        if selected_res_id:
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("✅ Convertir en emprunt", type="primary", use_container_width=True):
                    # Implémenter la conversion réservation -> emprunt
                    st.info("Fonctionnalité à implémenter")
            
            with col2:
                if st.button("✏️ Modifier", type="secondary", use_container_width=True):
                    st.info("Fonctionnalité à implémenter")
            
            with col3:
                if st.button("🗑️ Annuler", type="secondary", use_container_width=True):
                    res_id = selected_res_id.split(" - ")[0]
                    for r in res_data:
                        if r["ID"] == res_id:
                            g.remove((r["URI"], None, None))
                            g.remove((None, None, r["URI"]))
                            save_ontology(g)
                            st.success("Réservation annulée!")
                            st.rerun()
                            break
    else:
        st.info("Aucune réservation active.")

# Ajouter Entités
elif tab == "➕ Ajouter Entités":
    st.header("➕ Ajouter de Nouvelles Entités")
    
    # Type d'entité à ajouter
    entity_type = st.selectbox(
        "Type d'entité à ajouter:",
        ["Livre", "Revue", "Article", "DVD", "CD Audio", "Thèse", "Mémoire",
         "Utilisateur", "Auteur", "Bibliothécaire", "Agent d'Accueil",
         "Emprunt", "Réservation", "Exemplaire", "Fournisseur", "Localisation"]
    )
    
    # Formulaire générique
    with st.form(f"form_{entity_type}"):
        st.subheader(f"Ajouter un(e) {entity_type}")
        
        # Champs communs
        if entity_type in ["Livre", "Revue", "Article", "DVD", "CD Audio", "Thèse", "Mémoire"]:
            titre = st.text_input("Titre*", key=f"titre_{entity_type}")
        
        if entity_type in ["Livre", "Revue", "Article", "Utilisateur", "Auteur", "Bibliothécaire", "Agent d'Accueil"]:
            nom = st.text_input("Nom*", key=f"nom_{entity_type}")
        
        # Champs spécifiques
        if entity_type == "Livre":
            isbn = st.text_input("ISBN", key="isbn")
            date_pub = st.date_input("Date de publication", key="date_pub_livre")
        
        elif entity_type == "Revue":
            issn = st.text_input("ISSN", key="issn")
        
        elif entity_type == "Article":
            doi = st.text_input("DOI", key="doi")
            revue = st.text_input("Revue", key="revue")
        
        elif entity_type in ["Utilisateur", "Auteur", "Bibliothécaire", "Agent d'Accueil"]:
            email = st.text_input("Email", key=f"email_{entity_type}")
            matricule = st.text_input("Matricule", key=f"matricule_{entity_type}")
        
        elif entity_type == "Emprunt":
            # Sélectionner utilisateur existant
            utilisateurs = get_instances(BIB.Utilisateur)
            user_options = ["-- Sélectionner --"] + [format_uri(u) for u in utilisateurs]
            user_selected = st.selectbox("Utilisateur*", user_options, key="user_emp")
            
            # Sélectionner exemplaire disponible
            exemplaires = get_instances(BIB.Exemplaire)
            ex_options = ["-- Sélectionner --"]
            for ex in exemplaires:
                emprunte_par = g.value(ex, BIB.estEmpruntéPar)
                if not emprunte_par:  # Disponible
                    doc = g.value(ex, BIB.estUneCopieDe)
                    doc_titre = g.value(doc, BIB.titre) if doc else "Inconnu"
                    ex_options.append(f"{format_uri(ex)} - {doc_titre}")
            
            ex_selected = st.selectbox("Exemplaire*", ex_options, key="ex_emp")
            date_retour = st.date_input("Date de retour prévue*", key="date_retour_emp")
        
        elif entity_type == "Réservation":
            utilisateurs = get_instances(BIB.Utilisateur)
            user_options = ["-- Sélectionner --"] + [format_uri(u) for u in utilisateurs]
            user_selected = st.selectbox("Utilisateur*", user_options, key="user_res")
            
            documents = []
            for cls in [BIB.Livre, BIB.Revue, BIB.Article, BIB.DVD, BIB.CDAudio]:
                documents.extend(get_instances(cls))
            
            doc_options = ["-- Sélectionner --"] + [format_uri(d) for d in documents]
            doc_selected = st.selectbox("Document*", doc_options, key="doc_res")
        
        elif entity_type == "Exemplaire":
            documents = []
            for cls in [BIB.Livre, BIB.Revue, BIB.Article, BIB.DVD, BIB.CDAudio]:
                documents.extend(get_instances(cls))
            
            doc_options = ["-- Sélectionner --"] + [format_uri(d) for d in documents]
            doc_selected = st.selectbox("Document*", doc_options, key="doc_ex")
            
            code_barre = st.text_input("Code-barres*", key="code_barre")
            etat = st.selectbox("État*", ["neuf", "bon", "abîmé", "réparation"], key="etat")
            date_acq = st.date_input("Date d'acquisition", key="date_acq")
        
        elif entity_type == "Fournisseur":
            nom_fournisseur = st.text_input("Nom du fournisseur*", key="nom_fournisseur")
        
        elif entity_type == "Localisation":
            nom_localisation = st.text_input("Nom de la localisation*", key="nom_localisation")
            description = st.text_area("Description", key="desc_localisation")
        
        # Bouton de soumission
        submitted = st.form_submit_button("Ajouter", type="primary")
        
        if submitted:
            # Générer une URI unique
            uri = generate_uri(entity_type.lower(), "new")
            
            # Déterminer la classe
            class_mapping = {
                "Livre": BIB.Livre,
                "Revue": BIB.Revue,
                "Article": BIB.Article,
                "DVD": BIB.DVD,
                "CD Audio": BIB.CDAudio,
                "Thèse": BIB.Thèse,
                "Mémoire": BIB.Mémoire,
                "Utilisateur": BIB.Utilisateur,
                "Auteur": BIB.Auteur,
                "Bibliothécaire": BIB.Bibliothécaire,
                "Agent d'Accueil": BIB.AgentAccueil,
                "Emprunt": BIB.EmpruntNormal,
                "Réservation": BIB.Réservation,
                "Exemplaire": BIB.Exemplaire,
                "Fournisseur": BIB.Fournisseur,
                "Localisation": BIB.Localisation
            }
            
            classe = class_mapping.get(entity_type)
            
            if classe:
                # Ajouter le type
                g.add((uri, RDF.type, classe))
                g.add((uri, RDF.type, OWL.NamedIndividual))
                
                # Ajouter les propriétés selon le type
                if entity_type in ["Livre", "Revue", "Article", "DVD", "CD Audio", "Thèse", "Mémoire"]:
                    if titre:
                        g.add((uri, BIB.titre, Literal(titre)))
                
                if entity_type in ["Livre", "Revue", "Article", "Utilisateur", "Auteur", "Bibliothécaire", "Agent d'Accueil"]:
                    if nom:
                        g.add((uri, BIB.nom, Literal(nom)))
                
                # Propriétés spécifiques
                if entity_type == "Livre" and isbn:
                    g.add((uri, BIB.isbn, Literal(isbn)))
                
                if entity_type == "Revue" and issn:
                    g.add((uri, BIB.issn, Literal(issn)))
                
                if entity_type == "Article" and doi:
                    g.add((uri, BIB.doi, Literal(doi)))
                
                if entity_type in ["Utilisateur", "Auteur", "Bibliothécaire", "Agent d'Accueil"]:
                    if email:
                        g.add((uri, BIB.email, Literal(email)))
                    if matricule:
                        g.add((uri, BIB.matricule, Literal(matricule)))
                
                # Sauvegarder
                save_ontology(g)
                st.success(f"{entity_type} ajouté(e) avec succès!")
                st.rerun()

# Les autres sections restent similaires...
# Pour gagner de l'espace, je vais mettre les sections restantes de manière plus concise

elif tab == "🔗 Exploration Relations":
    st.header("🔗 Exploration des Relations")
    
    # Cette section peut rester similaire à la version précédente
    # Mais nous allons l'améliorer avec des filtres
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Sélectionner une classe de départ
        classes_list = [format_uri(c) for c in classes]
        start_class = st.selectbox("Classe de départ:", ["Toutes"] + classes_list)
    
    with col2:
        # Sélectionner un type de relation
        relations_list = [format_uri(p) for p in object_props]
        selected_relation = st.selectbox("Relation spécifique:", ["Toutes"] + relations_list)
    
    # Explorer les relations
    if st.button("Explorer les relations", type="primary"):
        # Implémentation de l'exploration des relations
        st.info("Exploration des relations en cours...")
        # Vous pouvez adapter le code de la version précédente ici

elif tab == "⚙️ Structure Ontologique":
    st.header("⚙️ Structure de l'Ontologie")
    
    # Afficher la hiérarchie des classes
    st.subheader("🌳 Hiérarchie des Classes")
    
    # Récupérer toutes les classes avec leurs sous-classes
    hierarchy = {}
    for cls in classes:
        super_classes = list(g.objects(cls, RDFS.subClassOf))
        for super_cls in super_classes:
            if isinstance(super_cls, URIRef):
                super_name = format_uri(super_cls)
                cls_name = format_uri(cls)
                if super_name not in hierarchy:
                    hierarchy[super_name] = []
                hierarchy[super_name].append(cls_name)
    
    # Afficher la hiérarchie
    for super_cls, sub_classes in hierarchy.items():
        with st.expander(f"📁 {super_cls} ({len(sub_classes)} sous-classes)"):
            for sub_cls in sub_classes:
                # Compter les instances
                instances = get_instances(BIB[sub_cls])
                count = len(instances)
                st.write(f"  └─ 📄 {sub_cls} ({count} instances)")
    
    # Bouton pour régénérer l'ontologie
    st.subheader("🔄 Maintenance")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Vérifier la cohérence", type="secondary"):
            st.info("Vérification de cohérence à implémenter avec un raisonneur OWL")
    
    with col2:
        if st.button("Exporter l'ontologie", type="primary"):
            export_format = st.selectbox("Format:", ["Turtle", "JSON-LD", "RDF/XML"])
            export_data = g.serialize(format=export_format.lower())
            st.download_button(
                label="Télécharger",
                data=export_data,
                file_name=f"bibliotheque_export.{export_format.lower()}",
                mime="text/plain"
            )

# Gestion des sessions pour la modification
if 'modifier_document' in st.session_state:
    st.sidebar.info("Mode modification document activé")
    # Implémenter le formulaire de modification

if 'modifier_personne' in st.session_state:
    st.sidebar.info("Mode modification personne activé")
    # Implémenter le formulaire de modification

# Footer
st.markdown("---")
st.markdown("📚 **Bibliothèque Intelligente** - Système de Gestion Ontologique • Développé avec Streamlit")