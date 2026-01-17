import streamlit as st
import pandas as pd
import plotly.express as px
from rdflib import Graph, Namespace, RDF, RDFS, OWL, XSD, Literal, URIRef
from datetime import datetime, timedelta
import uuid

# Configuration de la page
st.set_page_config(
    page_title="Bibliothèque Intelligente - Gestion Ontologique",
    page_icon="📚",
    layout="wide"
)

# Titre principal
st.title("📚 Système de Gestion Dynamique de Bibliothèque")
# st.markdown("### Gestion Complète de l'Ontologie Bibliothèque")

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

# # Statistiques dans la sidebar
# st.sidebar.header("📊 Statistiques de l'Ontologie")

# # Compter les classes
classes = list(g.subjects(RDF.type, OWL.Class))
# st.sidebar.metric("Classes", len(classes))

# # Compter les individus
individuals = list(g.subjects(RDF.type, OWL.NamedIndividual))
# st.sidebar.metric("Individus", len(individuals))

# # Compter les propriétés
object_props = list(g.subjects(RDF.type, OWL.ObjectProperty))
data_props = list(g.subjects(RDF.type, OWL.DatatypeProperty))
# st.sidebar.metric("Propriétés", len(object_props) + len(data_props))

# Navigation
st.sidebar.header("Navigation")
tab = st.sidebar.radio(
    "Sélectionnez une section:",
    ["📘 Instructions", "🏠 Tableau de Bord", "📖 Gestion Documents", "👥 Gestion Personnes", 
     "📋 Gestion Emprunts", "📝 Gestion Réservations", "➕ Ajouter Entités", 
     "🔗 Exploration Relations", "⚙️ Structure Ontologique"] 
)

# Tableau de Bord
if tab == "🏠 Tableau de Bord":
    st.header("Tableau de Bord de la Bibliothèque")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Compter tous les documents
        documents = []
        for doc_class in [BIB.Livre, BIB.Revue, BIB.Article, BIB.DVD, BIB.CDAudio, BIB.Thèse, BIB.Mémoire, BIB.RessourceÉlectronique]:
            documents.extend(get_instances(doc_class))
        st.metric("Documents", len(documents))
        
        # Types de documents
        doc_types = {}
        for doc_class in [BIB.Livre, BIB.Revue, BIB.Article, BIB.CDAudio, BIB.DVD, BIB.Thèse, BIB.Mémoire]:
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
        # Compter toutes les personnes
        personnes = []
        for pers_class in [BIB.Utilisateur, BIB.Employé, BIB.Auteur, BIB.Bibliothécaire, BIB.AgentAccueil]:
            personnes.extend(get_instances(pers_class))
        st.metric("Personnes", len(personnes))
        
        # Types de personnes
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
        
        # Compter les emprunts actifs (sans date de retour effective)
        emprunts_actifs = 0
        for emp in get_instances(BIB.Emprunt):
            date_retour_effective = g.value(emp, BIB.dateRetourEffective)
            if not date_retour_effective:
                emprunts_actifs += 1
        st.metric("Emprunts actifs", emprunts_actifs)
        
        reservations = get_instances(BIB.Réservation)
        st.metric("Réservations", len(reservations))

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

# Gestion Emprunts - SECTION CORRIGÉE
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
    
    # Si aucun emprunt spécifique trouvé, chercher tous les emprunts
    if not emprunts_data and emp_type == "Tous":
        for emp in get_instances(BIB.Emprunt):
            # Vérifier si c'est déjà dans un type spécifique
            if not ((emp, RDF.type, BIB.EmpruntNormal) in g or 
                   (emp, RDF.type, BIB.EmpruntRéservé) in g or 
                   (emp, RDF.type, BIB.EmpruntInterBibliothèque) in g):
                emprunts_data.append({"Type": "Non spécifié", "URI": emp})
    
    # Afficher les emprunts
    if emprunts_data:
        emp_display = []
        for emp in emprunts_data:
            utilisateur = g.value(emp["URI"], BIB.effectuéPar)
            user_name = g.value(utilisateur, BIB.nom) if utilisateur else format_uri(utilisateur) if utilisateur else "Inconnu"
            
            exemplaire = g.value(emp["URI"], BIB.concerneExemplaire)
            
            # Obtenir le document via l'exemplaire
            doc_titre = "Document inconnu"
            code_exemplaire = "N/A"
            
            if exemplaire:
                # Récupérer le code-barres de l'exemplaire
                code_exemplaire = g.value(exemplaire, BIB.codeBarre)
                if not code_exemplaire:
                    code_exemplaire = format_uri(exemplaire)
                
                # Récupérer le document lié à l'exemplaire
                doc = g.value(exemplaire, BIB.estUneCopieDe)
                if doc:
                    doc_titre = g.value(doc, BIB.titre)
                    if not doc_titre:
                        doc_titre = format_uri(doc)
                else:
                    doc_titre = f"Exemplaire {code_exemplaire}"
            else:
                doc_titre = "Exemplaire non spécifié"
            
            date_debut = g.value(emp["URI"], BIB.dateDébut)
            date_retour = g.value(emp["URI"], BIB.dateRetourPrévue)
            date_retour_effective = g.value(emp["URI"], BIB.dateRetourEffective)
            
            # Vérifier le statut
            if date_retour_effective:
                status = "✅ Retourné"
            else:
                status = "🟢 En cours"
                if date_retour:
                    try:
                        date_retour_dt = datetime.strptime(str(date_retour)[:10], "%Y-%m-%d")
                        if datetime.now() > date_retour_dt:
                            status = "🔴 En retard"
                    except:
                        pass
            
            emp_display.append({
                "Type": emp["Type"],
                "Utilisateur": str(user_name),
                "Document": str(doc_titre),
                "Exemplaire": str(code_exemplaire),
                "Date Début": str(date_debut)[:10] if date_debut else "N/A",
                "Date Retour": str(date_retour)[:10] if date_retour else "N/A",
                "Statut": status,
                "ID": format_uri(emp["URI"])
            })
        
        # Trier par date de retour (les plus urgents d'abord)
        emp_display.sort(key=lambda x: x["Date Retour"] if x["Date Retour"] != "N/A" else "9999-99-99")
        
        df_emp = pd.DataFrame(emp_display)
        st.dataframe(df_emp, use_container_width=True, hide_index=True)
        
        # Statistiques
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total emprunts", len(emp_display))
        with col2:
            en_retard = sum(1 for e in emp_display if e["Statut"] == "🔴 En retard")
            st.metric("En retard", en_retard, delta_color="inverse")
        with col3:
            retournes = sum(1 for e in emp_display if e["Statut"] == "✅ Retourné")
            st.metric("Retournés", retournes)
        
        # Gestion des retours
        st.subheader("📥 Gestion des Retours")
        
        if emp_display:
            # Filtrer les emprunts encore actifs (sans date de retour effective)
            emprunts_actifs = []
            for emp in emprunts_data:
                date_retour_effective = g.value(emp["URI"], BIB.dateRetourEffective)
                if not date_retour_effective:
                    emprunts_actifs.append(emp)
            
            if emprunts_actifs:
                # Créer la liste des emprunts actifs pour la sélection
                options_actifs = []
                for emp in emprunts_actifs:
                    utilisateur = g.value(emp["URI"], BIB.effectuéPar)
                    user_name = g.value(utilisateur, BIB.nom) if utilisateur else format_uri(utilisateur)
                    
                    exemplaire = g.value(emp["URI"], BIB.concerneExemplaire)
                    code_ex = g.value(exemplaire, BIB.codeBarre) if exemplaire else "N/A"
                    
                    options_actifs.append(f"{format_uri(emp['URI'])} - {user_name} (Ex: {code_ex})")
                
                selected_emp_option = st.selectbox(
                    "Sélectionnez un emprunt à retourner:",
                    options_actifs
                )
                
                if selected_emp_option and st.button("✅ Enregistrer le retour", type="primary"):
                    emp_id = selected_emp_option.split(" - ")[0]
                    
                    # Trouver l'URI de l'emprunt
                    emp_uri = None
                    for emp in emprunts_actifs:
                        if format_uri(emp["URI"]) == emp_id:
                            emp_uri = emp["URI"]
                            break
                    
                    if emp_uri:
                        try:
                            # Marquer la date de retour effective
                            now = datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
                            g.add((emp_uri, BIB.dateRetourEffective, Literal(now, datatype=XSD.dateTime)))
                            
                            # Libérer l'exemplaire
                            exemplaire = g.value(emp_uri, BIB.concerneExemplaire)
                            if exemplaire:
                                g.remove((exemplaire, BIB.estEmpruntéPar, None))
                            
                            save_ontology(g)
                            st.success("✅ Retour enregistré avec succès!")
                            
                            # Afficher un récapitulatif
                            utilisateur = g.value(emp_uri, BIB.effectuéPar)
                            user_name = g.value(utilisateur, BIB.nom) if utilisateur else format_uri(utilisateur)
                            
                            with st.expander("📋 Détails du retour"):
                                st.write(f"**Emprunt:** {format_uri(emp_uri)}")
                                st.write(f"**Utilisateur:** {user_name}")
                                st.write(f"**Date de retour:** {now[:10]}")
                                if exemplaire:
                                    code = g.value(exemplaire, BIB.codeBarre)
                                    st.write(f"**Exemplaire retourné:** {code if code else format_uri(exemplaire)}")
                            
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Erreur lors de l'enregistrement du retour: {str(e)}")
                    else:
                        st.error("❌ Emprunt non trouvé")
            else:
                st.info("✅ Tous les emprunts ont déjà été retournés!")
        else:
            st.info("Aucun emprunt à retourner.")
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
    
    # Récupérer les données existantes pour les listes déroulantes
    # Récupérer tous les auteurs existants
    auteurs_existants = get_instances(BIB.Auteur)
    auteurs_options = ["-- Créer un nouvel auteur --"] 
    for a in auteurs_existants:
        nom_auteur = g.value(a, BIB.nom)
        if nom_auteur:
            auteurs_options.append(f"{format_uri(a)} - {nom_auteur}")
    
    # Récupérer tous les utilisateurs existants
    utilisateurs_existants = get_instances(BIB.Utilisateur)
    utilisateurs_options = ["-- Sélectionner --"] 
    for u in utilisateurs_existants:
        nom_user = g.value(u, BIB.nom)
        if nom_user:
            utilisateurs_options.append(f"{nom_user} ({format_uri(u)})")
    
    # Récupérer tous les documents existants avec leurs titres
    documents_existants = []
    for cls in [BIB.Livre, BIB.Revue, BIB.Article, BIB.DVD, BIB.CDAudio, BIB.Thèse, BIB.Mémoire]:
        for doc in get_instances(cls):
            titre = g.value(doc, BIB.titre)
            if titre:
                documents_existants.append({
                    "URI": doc,
                    "Titre": str(titre),
                    "Type": format_uri(cls)
                })
    
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
        
        if entity_type in ["Utilisateur", "Auteur", "Bibliothécaire", "Agent d'Accueil"]:
            nom = st.text_input("Nom complet*", key=f"nom_{entity_type}")
        
        # Champs spécifiques pour LIVRE
        if entity_type == "Livre":
            col1, col2 = st.columns(2)
            
            with col1:
                isbn = st.text_input("ISBN (13 chiffres)", key="isbn")
                date_pub = st.date_input("Date de publication", key="date_pub_livre")
                editeur = st.text_input("Éditeur", key="editeur_livre")
            
            with col2:
                # Sélection/création d'auteur
                st.markdown("**Auteur**")
                choix_auteur = st.radio(
                    "Choisir l'auteur:",
                    ["Sélectionner un auteur existant", "Créer un nouvel auteur"],
                    key="choix_auteur"
                )
                
                if choix_auteur == "Sélectionner un auteur existant":
                    auteur_selectionne = st.selectbox(
                        "Auteur existant:",
                        auteurs_options,
                        key="auteur_existant"
                    )
                    nouvel_auteur_nom = None
                    nouvel_auteur_email = None
                else:
                    st.markdown("**Informations du nouvel auteur**")
                    nouvel_auteur_nom = st.text_input("Nom de l'auteur*", key="nouvel_auteur_nom")
                    nouvel_auteur_email = st.text_input("Email de l'auteur", key="nouvel_auteur_email")
                    auteur_selectionne = None
                
                # Sujet/Thématique
                sujet = st.text_input("Sujet/Thématique", key="sujet_livre")
        
        elif entity_type == "Revue":
            col1, col2 = st.columns(2)
            with col1:
                issn = st.text_input("ISSN", key="issn")
                periodicite = st.selectbox(
                    "Périodicité",
                    ["Quotidien", "Hebdomadaire", "Mensuel", "Bimestriel", "Trimestriel", "Annuel"],
                    key="periodicite"
                )
            with col2:
                annee_debut = st.number_input("Année de début", min_value=1800, max_value=2100, key="annee_debut")
                editeur_revue = st.text_input("Éditeur", key="editeur_revue")
        
        elif entity_type == "Article":
            col1, col2 = st.columns(2)
            with col1:
                doi = st.text_input("DOI", key="doi")
                pages = st.text_input("Pages (ex: 45-52)", key="pages_article")
            with col2:
                # Sélection de la revue
                revues = get_instances(BIB.Revue)
                revues_options = ["-- Sélectionner --"] 
                for r in revues:
                    titre_revue = g.value(r, BIB.titre)
                    if titre_revue:
                        revues_options.append(f"{titre_revue}")
                revue_selectionnee = st.selectbox("Revue*", revues_options, key="revue_article")
        
        elif entity_type in ["Utilisateur", "Auteur", "Bibliothécaire", "Agent d'Accueil"]:
            col1, col2 = st.columns(2)
            with col1:
                email = st.text_input("Email", key=f"email_{entity_type}")
                telephone = st.text_input("Téléphone", key=f"tel_{entity_type}")
            with col2:
                matricule = st.text_input("Matricule*", key=f"matricule_{entity_type}")
                date_inscription = st.date_input("Date d'inscription", key=f"date_inscr_{entity_type}")
                
                if entity_type == "Utilisateur":
                    statut = st.selectbox(
                        "Statut",
                        ["Actif", "Suspendu", "Désactivé"],
                        key="statut_utilisateur"
                    )
                    quota = st.number_input("Quota d'emprunts", min_value=1, max_value=20, value=5, key="quota")
        
        elif entity_type == "Emprunt":
            st.markdown("### Informations de l'emprunt")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Sélectionner utilisateur existant
                if utilisateurs_options:
                    user_selected = st.selectbox(
                        "Utilisateur*",
                        utilisateurs_options,
                        key="user_emp",
                        help="Sélectionnez l'utilisateur qui emprunte"
                    )
                else:
                    st.warning("⚠️ Aucun utilisateur existant. Veuillez d'abord créer un utilisateur.")
                    user_selected = None
            
            with col2:
                # Sélectionner exemplaire disponible
                exemplaires_disponibles = []
                exemplaires_tous = get_instances(BIB.Exemplaire)
                
                for ex in exemplaires_tous:
                    # Vérifier si l'exemplaire est déjà emprunté
                    emprunte_par = g.value(ex, BIB.estEmpruntéPar)
                    if not emprunte_par:  # Disponible
                        # Récupérer le document lié
                        doc = g.value(ex, BIB.estUneCopieDe)
                        doc_titre = "Sans titre"
                        if doc:
                            titre = g.value(doc, BIB.titre)
                            if titre:
                                doc_titre = str(titre)
                            else:
                                doc_titre = f"Document {format_uri(doc)}"
                        
                        code = g.value(ex, BIB.codeBarre)
                        if not code:
                            code = format_uri(ex)
                        
                        etat = g.value(ex, BIB.état) or "Inconnu"
                        
                        exemplaires_disponibles.append({
                            "URI": ex,
                            "Document": doc_titre,
                            "Code": code,
                            "État": etat,
                            "Document_URI": doc
                        })
                
                if exemplaires_disponibles:
                    ex_options = ["-- Sélectionner --"] + [
                        f"{ex['Document']} | Code: {ex['Code']} | État: {ex['État']}"
                        for ex in exemplaires_disponibles
                    ]
                    ex_selected = st.selectbox(
                        "Exemplaire*",
                        ex_options,
                        key="ex_emp",
                        help="Sélectionnez l'exemplaire à emprunter"
                    )
                    
                    # Afficher des détails sur l'exemplaire sélectionné
                    if ex_selected and ex_selected != "-- Sélectionner --":
                        selected_index = ex_options.index(ex_selected) - 1
                        selected_ex = exemplaires_disponibles[selected_index]
                        
                        with st.expander("📋 Détails de l'exemplaire sélectionné"):
                            st.write(f"**Document:** {selected_ex['Document']}")
                            st.write(f"**Code-barres:** {selected_ex['Code']}")
                            st.write(f"**État:** {selected_ex['État']}")
                            
                            # Afficher la localisation si disponible
                            localisation = g.value(selected_ex["URI"], BIB.estLocaliséÀ)
                            if localisation:
                                loc_nom = format_uri(localisation)
                                st.write(f"**Localisation:** {loc_nom}")
                else:
                    st.warning("⚠️ Aucun exemplaire disponible pour emprunt. Tous sont déjà empruntés ou en réparation.")
                    ex_selected = None
            
            col1, col2 = st.columns(2)
            with col1:
                date_debut = st.date_input("Date de début*", value=datetime.now().date(), key="date_debut_emp")
                duree = st.selectbox(
                    "Durée de l'emprunt",
                    ["7 jours", "14 jours", "21 jours", "30 jours"],
                    key="duree_emp"
                )
            with col2:
                # Calculer automatiquement la date de retour
                if duree:
                    jours = int(duree.split()[0])
                    date_retour_calculee = date_debut + timedelta(days=jours)
                    st.info(f"**Date de retour calculée:** {date_retour_calculee}")
                    date_retour = st.date_input(
                        "Date de retour prévue*",
                        value=date_retour_calculee,
                        key="date_retour_emp"
                    )
            
            # Type d'emprunt
            type_emprunt = st.selectbox(
                "Type d'emprunt",
                ["Normal", "Réservé", "Inter-bibliothèque"],
                key="type_emprunt"
            )
        
        elif entity_type == "Réservation":
            st.markdown("### Informations de la réservation")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Sélectionner utilisateur
                if utilisateurs_options:
                    user_selected = st.selectbox(
                        "Utilisateur*",
                        utilisateurs_options,
                        key="user_res"
                    )
                else:
                    st.warning("Aucun utilisateur existant.")
                    user_selected = None
            
            with col2:
                # Sélectionner document (afficher les titres)
                if documents_existants:
                    doc_options = ["-- Sélectionner --"] + [
                        f"{doc['Titre']} ({doc['Type']})"
                        for doc in documents_existants
                    ]
                    doc_selected = st.selectbox(
                        "Document*",
                        doc_options,
                        key="doc_res"
                    )
                else:
                    st.warning("Aucun document existant.")
                    doc_selected = None
            
            # Date de réservation
            date_reservation = st.date_input(
                "Date de réservation*",
                value=datetime.now().date(),
                key="date_res"
            )
            
            # Priorité
            priorite = st.selectbox(
                "Priorité",
                ["Normale", "Haute", "Urgente"],
                key="priorite_res"
            )
        
        elif entity_type == "Exemplaire":
            st.markdown("### Informations de l'exemplaire")
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Sélectionner document
                if documents_existants:
                    doc_options = ["-- Sélectionner --"] + [
                        f"{doc['Titre']} ({doc['Type']})"
                        for doc in documents_existants
                    ]
                    doc_selected = st.selectbox(
                        "Document*",
                        doc_options,
                        key="doc_ex"
                    )
                else:
                    st.warning("Aucun document existant.")
                    doc_selected = None
                
                code_barre = st.text_input("Code-barres*", key="code_barre")
                format_ex = st.selectbox(
                    "Format",
                    ["Physique", "Numérique", "Audio", "Vidéo"],
                    key="format_ex"
                )
            
            with col2:
                etat = st.selectbox(
                    "État*",
                    ["Neuf", "Très bon", "Bon", "Moyen", "Mauvais", "À réparer", "Perdu"],
                    key="etat"
                )
                
                date_acq = st.date_input(
                    "Date d'acquisition",
                    value=datetime.now().date(),
                    key="date_acq"
                )
                
                prix = st.number_input(
                    "Prix d'acquisition (€)",
                    min_value=0.0,
                    value=0.0,
                    step=0.5,
                    key="prix_ex"
                )
            
            # Localisation
            localisations = get_instances(BIB.Localisation)
            if localisations:
                loc_options = ["-- Non localisé --"] + [format_uri(loc) for loc in localisations]
                localisation = st.selectbox("Localisation", loc_options, key="loc_ex")
            else:
                st.info("Aucune localisation existante. L'exemplaire sera non localisé.")
        
        elif entity_type == "Fournisseur":
            col1, col2 = st.columns(2)
            with col1:
                nom_fournisseur = st.text_input("Nom du fournisseur*", key="nom_fournisseur")
                contact = st.text_input("Contact", key="contact_fournisseur")
            with col2:
                email_fournisseur = st.text_input("Email", key="email_fournisseur")
                telephone_fournisseur = st.text_input("Téléphone", key="tel_fournisseur")
        
        elif entity_type == "Localisation":
            col1, col2 = st.columns(2)
            with col1:
                nom_localisation = st.text_input("Nom de la localisation*", key="nom_localisation")
                batiment = st.text_input("Bâtiment", key="batiment")
            with col2:
                etagere = st.text_input("Étagère/Rayon", key="etagere")
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
                try:
                    # Ajouter le type
                    g.add((uri, RDF.type, classe))
                    g.add((uri, RDF.type, OWL.NamedIndividual))
                    
                    # Ajouter les propriétés selon le type
                    if entity_type == "Livre":
                        if titre:
                            g.add((uri, BIB.titre, Literal(titre)))
                        
                        if isbn:
                            g.add((uri, BIB.isbn, Literal(isbn)))
                        
                        # Gestion de l'auteur
                        if choix_auteur == "Sélectionner un auteur existant" and auteur_selectionne != "-- Créer un nouvel auteur --":
                            # Trouver l'URI de l'auteur sélectionné
                            auteur_uri_str = auteur_selectionne.split(" - ")[0]
                            auteur_uri = BIB[auteur_uri_str]
                            g.add((uri, BIB.aPourAuteur, auteur_uri))
                        elif choix_auteur == "Créer un nouvel auteur" and nouvel_auteur_nom:
                            # Créer un nouvel auteur
                            auteur_uri = generate_uri("auteur", "new")
                            g.add((auteur_uri, RDF.type, BIB.Auteur))
                            g.add((auteur_uri, RDF.type, OWL.NamedIndividual))
                            g.add((auteur_uri, BIB.nom, Literal(nouvel_auteur_nom)))
                            if nouvel_auteur_email:
                                g.add((auteur_uri, BIB.email, Literal(nouvel_auteur_email)))
                            g.add((uri, BIB.aPourAuteur, auteur_uri))
                        
                        if date_pub:
                            g.add((uri, BIB.datePublication, Literal(date_pub.isoformat(), datatype=XSD.dateTime)))
                    
                    elif entity_type == "Emprunt":
                        # Gérer l'utilisateur
                        if user_selected and user_selected != "-- Sélectionner --":
                            user_uri_str = user_selected.split("(")[1].replace(")", "")
                            user_uri = BIB[user_uri_str]
                            g.add((uri, BIB.effectuéPar, user_uri))
                            g.add((user_uri, BIB.aPourEmprunt, uri))
                        
                        # Gérer l'exemplaire
                        if ex_selected and ex_selected != "-- Sélectionner --":
                            selected_index = ex_options.index(ex_selected) - 1
                            selected_ex = exemplaires_disponibles[selected_index]
                            ex_uri = selected_ex["URI"]
                            
                            g.add((uri, BIB.concerneExemplaire, ex_uri))
                            
                            # Marquer l'exemplaire comme emprunté
                            if user_selected and user_selected != "-- Sélectionner --":
                                user_uri_str = user_selected.split("(")[1].replace(")", "")
                                user_uri = BIB[user_uri_str]
                                g.add((ex_uri, BIB.estEmpruntéPar, user_uri))
                        
                        # Ajouter les dates
                        if date_debut:
                            g.add((uri, BIB.dateDébut, Literal(date_debut.isoformat(), datatype=XSD.dateTime)))
                        
                        if date_retour:
                            g.add((uri, BIB.dateRetourPrévue, Literal(date_retour.isoformat(), datatype=XSD.dateTime)))
                        
                        # Définir le type d'emprunt
                        if type_emprunt == "Réservé":
                            g.add((uri, RDF.type, BIB.EmpruntRéservé))
                        elif type_emprunt == "Inter-bibliothèque":
                            g.add((uri, RDF.type, BIB.EmpruntInterBibliothèque))
                    
                    elif entity_type == "Réservation":
                        # Gérer l'utilisateur
                        if user_selected and user_selected != "-- Sélectionner --":
                            user_uri_str = user_selected.split("(")[1].replace(")", "")
                            user_uri = BIB[user_uri_str]
                            g.add((uri, BIB.aPourRéservation, user_uri))
                        
                        # Gérer le document
                        if doc_selected and doc_selected != "-- Sélectionner --":
                            # Trouver l'URI du document sélectionné
                            doc_titre = doc_selected.split(" (")[0]
                            for doc_data in documents_existants:
                                if doc_data["Titre"] == doc_titre:
                                    doc_uri = doc_data["URI"]
                                    g.add((uri, BIB.porteSur, doc_uri))
                                    break
                        
                        if date_reservation:
                            g.add((uri, BIB.dateReservation, Literal(date_reservation.isoformat(), datatype=XSD.dateTime)))
                    
                    elif entity_type == "Exemplaire":
                        # Gérer le document
                        if doc_selected and doc_selected != "-- Sélectionner --":
                            doc_titre = doc_selected.split(" (")[0]
                            for doc_data in documents_existants:
                                if doc_data["Titre"] == doc_titre:
                                    doc_uri = doc_data["URI"]
                                    g.add((uri, BIB.estUneCopieDe, doc_uri))
                                    break
                        
                        if code_barre:
                            g.add((uri, BIB.codeBarre, Literal(code_barre)))
                        
                        if etat:
                            g.add((uri, BIB.état, Literal(etat)))
                        
                        if date_acq:
                            g.add((uri, BIB.dateAcquisition, Literal(date_acq.isoformat(), datatype=XSD.dateTime)))
                        
                        # Gérer la localisation
                        if 'localisation' in locals() and localisation and localisation != "-- Non localisé --":
                            loc_uri = BIB[localisation]
                            g.add((uri, BIB.estLocaliséÀ, loc_uri))
                    
                    # Ajouter les propriétés communes
                    if entity_type in ["Livre", "Revue", "Article", "DVD", "CD Audio", "Thèse", "Mémoire"] and 'titre' in locals() and titre:
                        g.add((uri, BIB.titre, Literal(titre)))
                    
                    if entity_type in ["Utilisateur", "Auteur", "Bibliothécaire", "Agent d'Accueil"] and 'nom' in locals() and nom:
                        g.add((uri, BIB.nom, Literal(nom)))
                    
                    if entity_type in ["Utilisateur", "Auteur", "Bibliothécaire", "Agent d'Accueil"] and 'email' in locals() and email:
                        g.add((uri, BIB.email, Literal(email)))
                    
                    if entity_type in ["Utilisateur", "Auteur", "Bibliothécaire", "Agent d'Accueil"] and 'matricule' in locals() and matricule:
                        g.add((uri, BIB.matricule, Literal(matricule)))
                    
                    # Sauvegarder
                    save_ontology(g)
                    st.success(f"✅ {entity_type} ajouté(e) avec succès!")
                    
                    # Afficher un récapitulatif
                    with st.expander("📋 Voir les détails ajoutés"):
                        properties = list(g.predicate_objects(uri))
                        recap = {
                            "Type": entity_type,
                            "URI": str(uri),
                            "Classe": format_uri(classe),
                            "Propriétés ajoutées": len(properties)
                        }
                        st.json(recap)
                    
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Erreur lors de l'ajout: {str(e)}")
                    import traceback
                    st.code(traceback.format_exc())

# Exploration Relations
elif tab == "🔗 Exploration Relations":
    st.header("🔗 Exploration des Relations")
    
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
        st.info("Exploration des relations en cours...")
        
        # Implémentation basique de l'exploration
        triplets = []
        if selected_relation == "Toutes":
            for prop in object_props:
                for s, o in g.subject_objects(prop):
                    triplets.append({
                        "Sujet": format_uri(s),
                        "Relation": format_uri(prop),
                        "Objet": format_uri(o)
                    })
        else:
            # Trouver la propriété spécifique
            for prop in object_props:
                if format_uri(prop) == selected_relation:
                    for s, o in g.subject_objects(prop):
                        triplets.append({
                            "Sujet": format_uri(s),
                            "Relation": format_uri(prop),
                            "Objet": format_uri(o)
                        })
                    break
        
        if triplets:
            df_triplets = pd.DataFrame(triplets)
            st.dataframe(df_triplets, use_container_width=True)
            
            # Statistiques
            st.metric("Nombre de relations trouvées", len(triplets))
        else:
            st.warning("Aucune relation trouvée avec ces critères.")

# Structure Ontologique
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

# Instructions
elif tab == "📘 Instructions":
    st.header("📘 Guide d'Utilisation de la Plateforme")
    
    st.markdown("""
    ## Bienvenue dans le Système de Gestion de Bibliothèque Ontologique
    
    Cette plateforme vous permet de gérer une bibliothèque intelligente basée sur une ontologie RDF.
    Voici comment utiliser chaque section :
    """)
    
    # Table des matières
    with st.expander("📋 **Table des Matières**", expanded=True):
        st.markdown("""
        1. [🏠 Tableau de Bord](#tableau-de-bord)
        2. [📖 Gestion des Documents](#gestion-des-documents)
        3. [👥 Gestion des Personnes](#gestion-des-personnes)
        4. [📋 Gestion des Emprunts](#gestion-des-emprunts)
        5. [📝 Gestion des Réservations](#gestion-des-réservations)
        6. [➕ Ajouter des Entités](#ajouter-des-entités)
        7. [🔗 Exploration des Relations](#exploration-des-relations)
        8. [⚙️ Structure Ontologique](#structure-ontologique)
        9. [💾 Sauvegarde et Export](#sauvegarde-et-export)
        10. [🚨 Dépannage](#dépannage)
        """)
    
    # Section 1: Tableau de Bord
    st.markdown("---")
    st.markdown('<a name="tableau-de-bord"></a>', unsafe_allow_html=True)
    st.subheader("🏠 Tableau de Bord")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("""
        **Fonction :** Vue d'ensemble de la bibliothèque
        
        **Ce que vous pouvez voir :**
        - 📊 Statistiques générales (documents, personnes, exemplaires)
        - 📈 Graphiques de répartition par type
        - 🔢 Nombre d'emprunts actifs et réservations
        
        **Actions possibles :**
        - Aucune modification, seulement visualisation
        - Les graphiques sont interactifs (zoom, survol)
        """)
    with col2:
        st.info("💡 **Astuce :** Utilisez cette section pour un suivi rapide de l'état de votre bibliothèque.")
    
    # Section 2: Gestion Documents
    st.markdown("---")
    st.markdown('<a name="gestion-des-documents"></a>', unsafe_allow_html=True)
    st.subheader("📖 Gestion des Documents")
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("""
        **Fonction :** Gérer tous les types de documents
        
        **Fonctionnalités :**
        - 🔍 Rechercher par titre, auteur ou identifiant
        - 🏷️ Filtrer par type (Livres, Revues, Articles, etc.)
        - 👁️ Voir les détails complets d'un document
        - 📋 Lister les exemplaires avec leur statut
        - 🗑️ Supprimer ou ✏️ modifier un document
        
        **Types de documents :**
        - Livre (avec ISBN)
        - Revue (avec ISSN)
        - Article (avec DOI)
        - DVD, CD Audio
        - Thèse, Mémoire
        """)
    with col2:
        st.warning("⚠️ **Attention :** La suppression d'un document supprime aussi tous ses exemplaires associés.")
    
    # Section 3: Gestion Personnes
    st.markdown("---")
    st.markdown('<a name="gestion-des-personnes"></a>', unsafe_allow_html=True)
    st.subheader("👥 Gestion des Personnes")
    st.markdown("""
    **Fonction :** Gérer les utilisateurs, employés et auteurs
    
    **Catégories disponibles :**
    
    | Type | Description | Actions possibles |
    |------|-------------|-------------------|
    | **Utilisateur** | Emprunteurs de documents | Voir emprunts en cours, modifier, supprimer |
    | **Bibliothécaire** | Personnel de bibliothèque | Gérer les emprunts, modifier informations |
    | **Agent d'Accueil** | Personnel d'accueil | Modifier informations |
    | **Auteur** | Créateurs de documents | Associer à des documents, modifier |
    
    **Fonctionnalités :**
    - 🔍 Recherche par nom
    - 📋 Filtrage par type de personne
    - 📖 Visualisation des emprunts en cours (pour utilisateurs)
    """)
    
    # Section 4: Gestion Emprunts
    st.markdown("---")
    st.markdown('<a name="gestion-des-emprunts"></a>', unsafe_allow_html=True)
    st.subheader("📋 Gestion des Emprunts")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Types d'emprunts :**
        - 🟢 **Normal** : Emprunt standard
        - 🔵 **Réservé** : Emprunt suite à réservation
        - 🟣 **Inter-bibliothèque** : Prêt entre bibliothèques
        
        **Statuts visuels :**
        - 🟢 **En cours** : Emprunt actif dans les délais
        - 🔴 **En retard** : Date de retour dépassée
        - ✅ **Retourné** : Emprunt terminé
        """)
    with col2:
        st.markdown("""
        **Fonctionnalités :**
        - 📊 Statistiques en temps réel
        - 📅 Tri automatique par date de retour
        - ✅ Enregistrement des retours
        - 📋 Détails complets de chaque emprunt
        
        **Processus de retour :**
        1. Sélectionnez l'emprunt à retourner
        2. Cliquez sur "✅ Enregistrer le retour"
        3. Le système met à jour automatiquement
        """)
    
    # Section 5: Gestion Réservations
    st.markdown("---")
    st.markdown('<a name="gestion-des-réservations"></a>', unsafe_allow_html=True)
    st.subheader("📝 Gestion des Réservations")
    st.markdown("""
    **Fonction :** Gérer les réservations de documents
    
    **Informations affichées :**
    - 👤 Utilisateur ayant réservé
    - 📖 Document réservé
    - 📅 Date de réservation
    
    **Actions possibles :**
    - ✅ Convertir une réservation en emprunt
    - ✏️ Modifier une réservation
    - 🗑️ Annuler une réservation
    
    **Priorités disponibles :**
    - Normale
    - Haute
    - Urgente
    """)
    
    # Section 6: Ajouter Entités
    st.markdown("---")
    st.markdown('<a name="ajouter-des-entités"></a>', unsafe_allow_html=True)
    st.subheader("➕ Ajouter des Entités")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Types d'entités que vous pouvez ajouter :**
        
        **📚 Documents :**
        - Livre, Revue, Article
        - DVD, CD Audio
        - Thèse, Mémoire
        
        **👥 Personnes :**
        - Utilisateur, Auteur
        - Bibliothécaire, Agent d'Accueil
        
        **🔄 Activités :**
        - Emprunt, Réservation
        
        **🏷️ Autres :**
        - Exemplaire
        - Fournisseur
        - Localisation
        """)
    with col2:
        st.markdown("""
        **Caractéristiques des formulaires :**
        - ✳️ Champs obligatoires marqués par *
        - 🔄 Génération automatique d'URI uniques
        - ✅ Validation des données
        - 💾 Sauvegarde automatique
        
        **Workflow recommandé :**
        1. Créer d'abord les **Auteurs**
        2. Puis créer les **Documents**
        3. Ensuite créer les **Exemplaires**
        4. Créer les **Utilisateurs**
        5. Enfin créer les **Emprunts**
        """)
    
    # Section 7: Exploration Relations
    st.markdown("---")
    st.markdown('<a name="exploration-des-relations"></a>', unsafe_allow_html=True)
    st.subheader("🔗 Exploration des Relations")
    st.markdown("""
    **Fonction :** Explorer les liens sémantiques entre les entités
    
    **Comment ça marche :**
    1. Sélectionnez une **classe de départ** (ou "Toutes")
    2. Choisissez une **relation spécifique** (ou "Toutes")
    3. Cliquez sur "Explorer les relations"
    
    **Ce que vous verrez :**
    - 📊 Tableau des triplets RDF
    - 🔗 Relations Sujet → Prédicat → Objet
    - 📈 Statistiques du nombre de relations
    
    **Exemples de relations :**
    - `estUneCopieDe` : Lie un exemplaire à un document
    - `aPourAuteur` : Lie un document à un auteur
    - `effectuéPar` : Lie un emprunt à un utilisateur
    """)
    
    # Section 8: Structure Ontologique
    st.markdown("---")
    st.markdown('<a name="structure-ontologique"></a>', unsafe_allow_html=True)
    st.subheader("⚙️ Structure Ontologique")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("""
        **Hiérarchie des classes :**
        - 🌳 Vue arborescente des classes
        - 📊 Nombre d'instances par classe
        - 🔍 Navigation par expanders
        
        **Classes principales :**
        ```
        Document
        ├── Livre
        ├── Revue
        ├── Article
        └── ...
        
        Personne
        ├── Utilisateur
        ├── Employé
        └── Auteur
        
        Activité
        ├── Emprunt
        └── Réservation
        ```
        """)
    with col2:
        st.markdown("""
        **Outils de maintenance :**
        - 🔄 Vérification de cohérence
        - 💾 Export de l'ontologie
        
        **Formats d'export :**
        - Turtle (.ttl)
        - JSON-LD (.jsonld)
        - RDF/XML (.rdf)
        
        **Usage recommandé :**
        - Exporter régulièrement pour backup
        - Vérifier la hiérarchie avant d'ajouter des entités
        """)
    
    # Section 9: Sauvegarde et Export
    st.markdown("---")
    st.markdown('<a name="sauvegarde-et-export"></a>', unsafe_allow_html=True)
    st.subheader("💾 Sauvegarde et Export")
    st.markdown("""
    **Sauvegarde automatique :**
    - ✅ Toutes les modifications sont sauvegardées automatiquement
    - 📁 Fichier : `bibio.ttl` (format Turtle)
    - 🔄 Pas besoin d'action manuelle
    
    **Export manuel :**
    1. Allez dans **⚙️ Structure Ontologique**
    2. Cliquez sur **"Exporter l'ontologie"**
    3. Choisissez le format désiré
    4. Téléchargez le fichier
    
    **Bonnes pratiques :**
    - Faire un export avant des opérations critiques
    - Conserver des backups réguliers
    - Exporter en différents formats pour compatibilité
    """)
    
    # Section 10: Dépannage
    st.markdown("---")
    st.markdown('<a name="dépannage"></a>', unsafe_allow_html=True)
    st.subheader("🚨 Dépannage")
    
    with st.expander("❓ **Questions fréquentes**"):
        st.markdown("""
        **Q : Mon changement n'apparaît pas ?**
        R : Cliquez sur le bouton "🔄" en haut à droite ou utilisez F5.
        
        **Q : Je ne trouve pas une entité ?**
        R : Vérifiez les filtres et utilisez la recherche (insensible à la casse).
        
        **Q : Erreur lors de l'ajout ?**
        R : Vérifiez que tous les champs obligatoires (*) sont remplis.
        
        **Q : L'application est lente ?**
        R : Réduisez le nombre d'entités affichées avec les filtres.
        """)
    
    with st.expander("⚠️ **Problèmes courants et solutions**"):
        st.markdown("""
        | Problème | Solution |
        |----------|----------|
        | Données non affichées | Vérifiez les filtres, rafraîchissez la page |
        | Erreur de sauvegarde | Vérifiez les permissions du fichier bibio.ttl |
        | Formulaire ne se soumet pas | Tous les champs * doivent être remplis |
        | Graphique non mis à jour | Cliquez ailleurs sur la page pour forcer le refresh |
        | Liste déroulante vide | Créez d'abord les entités nécessaires |
        """)
    
    with st.expander("📞 **Support et Contact**"):
        st.markdown("""
        **En cas de problème persistant :**
        
        1. **Consultez les logs :**
           - Ouvrez les outils de développement (F12)
           - Vérifiez la console pour les erreurs
        
        2. **Vérifiez les données :**
           - Exportez l'ontologie
           - Ouvrez le fichier dans un éditeur de texte
        
        3. **Réinitialisation :**
           - Supprimez le fichier `bibio.ttl`
           - Redémarrez l'application
           - Recréez vos données
        
        **Pour rapporter un bug :**
        - Notez les étapes précises pour reproduire le problème
        - Capturez d'éventuels messages d'erreur
        - Indiquez votre navigateur et système d'exploitation
        """)
    
    # Conseils finaux
    st.markdown("---")
    st.success("""
    ### 🎯 Conseils pour une utilisation optimale :
    
    1. **Commencez simple** : Ajoutez d'abord quelques entités pour vous familiariser
    2. **Utilisez les filtres** : Ils accélèrent la navigation dans les grandes listes
    3. **Faites des backups** : Exportez régulièrement vos données
    4. **Explorez les relations** : Comprenez comment les entités sont liées
    5. **Testez le cycle complet** : Créez un document → exemplaire → utilisateur → emprunt → retour
    
    **Bonne utilisation de la plateforme !** 📚✨
    """)
    
    # Information système
    with st.expander("ℹ️ **Informations système**"):
        import sys, platform
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("**Python :**", sys.version.split()[0])
        with col2:
            st.write("**Streamlit :**", st.__version__)
        with col3:
            st.write("**Système :**", platform.system())
        
        # Vérification des packages
        try:
            import pandas as pd
            import plotly.express as px
            from rdflib import __version__ as rdflib_version
            st.write("**Pandas :**", pd.__version__)
            st.write("**Plotly :**", px.__version__)
            st.write("**RDFlib :**", rdflib_version)
            st.success("✅ Tous les packages sont correctement installés")
        except Exception as e:
            st.error(f"❌ Erreur : {e}")
            
# Gestion des sessions pour la modification
if 'modifier_document' in st.session_state:
    st.sidebar.info("Mode modification document activé")

if 'modifier_personne' in st.session_state:
    st.sidebar.info("Mode modification personne activé")

# Footer
st.markdown("---")
st.markdown("**Bibliothèque Intelligente** - Système de Gestion Ontologique • Développé avec Streamlit")