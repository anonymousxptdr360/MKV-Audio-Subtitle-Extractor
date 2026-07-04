import os
import subprocess
import json
import customtkinter as ctk
from tkinter import filedialog

EXTENSIONS_VIDEO = (".mkv", ".mp4", ".avi", ".mov", ".m4v", ".webm", ".flv", ".wmv")

NOMS_LANGUES = {
    "fre": "Français", "fra": "Français", "eng": "Anglais", "spa": "Espagnol",
    "ger": "Allemand", "deu": "Allemand", "ita": "Italien", "jpn": "Japonais",
    "kor": "Coréen", "chi": "Chinois", "zho": "Chinois", "por": "Portugais",
    "rus": "Russe", "ara": "Arabe", "dut": "Néerlandais", "nld": "Néerlandais",
    "swe": "Suédois", "pol": "Polonais", "tur": "Turc", "und": "Indéterminée",
}

def libelle_langue(code):
    return f"{NOMS_LANGUES.get(code, code)} ({code})"

def code_depuis_libelle(libelle):
    if "(" in libelle and libelle.endswith(")"):
        return libelle.split("(")[-1][:-1]
    return None

parametres = {"mkvmerge": r"C:\Users\user\Desktop\mkv\mkvtoolnix\mkvmerge.exe"}
etat = {"mode": None, "dossier": None, "fichiers": []}

app = ctk.CTk()
app.title("Trieur Audio/Sous-titres")
app.geometry("600x680")

def obtenir_liste_fichiers():
    if etat["mode"] == "dossier" and etat["dossier"]:
        return [os.path.join(etat["dossier"], f) for f in os.listdir(etat["dossier"]) if f.lower().endswith(EXTENSIONS_VIDEO)]
    elif etat["mode"] == "fichiers":
        return etat["fichiers"]
    return []

def detecter_langues(chemins):
    langues_audio, langues_st = [], []
    for chemin in chemins:
        try:
            r = subprocess.run([parametres["mkvmerge"], "-J", chemin], capture_output=True, text=True, encoding="utf-8")
            data = json.loads(r.stdout)
            for piste in data["tracks"]:
                l = piste["properties"].get("language", "und")
                if piste["type"] == "audio" and l not in langues_audio:
                    langues_audio.append(l)
                if piste["type"] == "subtitles" and l not in langues_st:
                    langues_st.append(l)
        except Exception:
            continue
    return langues_audio, langues_st

def mettre_a_jour_langues():
    liste = obtenir_liste_fichiers()
    if not liste:
        return
    zone_log.insert("end", "🔍 Détection des langues disponibles...\n")
    zone_log.see("end")
    app.update()

    langues_audio, langues_st = detecter_langues(liste)

    if langues_audio:
        libelles = [libelle_langue(c) for c in langues_audio]
        menu_langue_audio.configure(values=libelles)
        menu_langue_audio.set(libelles[0])
        zone_log.insert("end", f"   Audio trouvé : {', '.join(langues_audio)}\n")
    else:
        menu_langue_audio.configure(values=["Aucune langue détectée"])
        menu_langue_audio.set("Aucune langue détectée")

    if langues_st:
        libelles_st = [libelle_langue(c) for c in langues_st]
        menu_langue_soustitres.configure(values=libelles_st)
        menu_langue_soustitres.set(libelles_st[0])
        zone_log.insert("end", f"   Sous-titres trouvés : {', '.join(langues_st)}\n")
    else:
        menu_langue_soustitres.configure(values=["Aucun sous-titre détecté"])
        menu_langue_soustitres.set("Aucun sous-titre détecté")

    zone_log.see("end")

def choisir_dossier():
    dossier = filedialog.askdirectory(title="Choisis le dossier des vidéos")
    if dossier:
        etat["mode"] = "dossier"
        etat["dossier"] = dossier
        label_selection.configure(text=f"📁 Dossier : {dossier}")
        mettre_a_jour_langues()

def choisir_fichiers():
    fichiers = filedialog.askopenfilenames(
        title="Choisis une ou plusieurs vidéos",
        filetypes=[("Fichiers vidéo", "*.mkv *.mp4 *.avi *.mov *.m4v *.webm *.flv *.wmv"), ("Tous les fichiers", "*.*")]
    )
    if fichiers:
        etat["mode"] = "fichiers"
        etat["fichiers"] = list(fichiers)
        label_selection.configure(text=f"🎬 {len(fichiers)} fichier(s) sélectionné(s)")
        mettre_a_jour_langues()

def choisir_sortie():
    dossier = filedialog.askdirectory(title="Choisis le dossier de sortie")
    if dossier:
        entree_sortie.delete(0, "end")
        entree_sortie.insert(0, dossier)

def ouvrir_parametres():
    fen = ctk.CTkToplevel(app)
    fen.title("Paramètres")
    fen.geometry("450x180")
    fen.attributes("-topmost", True)
    ctk.CTkLabel(fen, text="Emplacement de mkvmerge.exe :").pack(pady=(25, 5))
    cadre = ctk.CTkFrame(fen, fg_color="transparent")
    cadre.pack(fill="x", padx=20)
    entree_mkv = ctk.CTkEntry(cadre)
    entree_mkv.insert(0, parametres["mkvmerge"])
    entree_mkv.pack(side="left", fill="x", expand=True, padx=(0, 10))

    def choisir_mkvmerge():
        chemin = filedialog.askopenfilename(title="Choisis mkvmerge.exe", filetypes=[("Exécutable", "*.exe")])
        if chemin:
            entree_mkv.delete(0, "end")
            entree_mkv.insert(0, chemin)
            parametres["mkvmerge"] = chemin

    ctk.CTkButton(cadre, text="Parcourir", command=choisir_mkvmerge, width=100).pack(side="left")

def lancer():
    liste = obtenir_liste_fichiers()
    if not liste:
        zone_log.insert("end", "⚠️ Choisis d'abord un dossier ou des fichiers.\n")
        return

    dossier_sortie = entree_sortie.get()
    langue_audio = code_depuis_libelle(menu_langue_audio.get())
    garder_sous_titres = case_sous_titres.get()
    langue_st = code_depuis_libelle(menu_langue_soustitres.get()) if garder_sous_titres else None
    mkvmerge = parametres["mkvmerge"]

    if not dossier_sortie:
        zone_log.insert("end", "⚠️ Choisis un dossier de sortie.\n")
        return
    if not langue_audio:
        zone_log.insert("end", "⚠️ Sélectionne une langue audio valide.\n")
        return

    os.makedirs(dossier_sortie, exist_ok=True)
    nb_total = len(liste)
    nb_succes = 0

    for chemin_video in liste:
        nom_fichier = os.path.basename(chemin_video)
        zone_log.insert("end", f"Traitement : {nom_fichier}...\n")
        zone_log.see("end")
        app.update()

        r = subprocess.run([mkvmerge, "-J", chemin_video], capture_output=True, text=True, encoding="utf-8")
        data = json.loads(r.stdout)

        id_audio, id_sous_titre = None, None
        for piste in data["tracks"]:
            l = piste["properties"].get("language", "")
            if piste["type"] == "audio" and l == langue_audio and id_audio is None:
                id_audio = piste["id"]
            if langue_st and piste["type"] == "subtitles" and l == langue_st and id_sous_titre is None:
                id_sous_titre = piste["id"]

        if id_audio is None:
            zone_log.insert("end", f"   ⚠️ Pas de piste audio '{langue_audio}', ignoré.\n")
            zone_log.see("end")
            continue

        nom_base = os.path.splitext(nom_fichier)[0]
        chemin_sortie = os.path.join(dossier_sortie, nom_base + ".mkv")

        commande = [mkvmerge, "-o", chemin_sortie, "--audio-tracks", str(id_audio)]
        if garder_sous_titres and id_sous_titre is not None:
            commande += ["--subtitle-tracks", str(id_sous_titre)]
        else:
            if garder_sous_titres and langue_st:
                zone_log.insert("end", f"   ℹ️ Pas de sous-titre '{langue_st}' pour ce fichier, sortie sans sous-titres.\n")
            commande += ["-S"]
        commande.append(chemin_video)

        subprocess.run(commande, capture_output=True, text=True, encoding="utf-8")
        nb_succes += 1
        zone_log.insert("end", "   ✅ Terminé.\n")
        zone_log.see("end")
        app.update()

    if nb_total > 1:
        zone_log.insert("end", f"\n🎉🎉🎉 TOUTES LES VIDÉOS ONT ÉTÉ TRAITÉES : {nb_succes}/{nb_total} réussies 🎉🎉🎉\n")
    else:
        zone_log.insert("end", "\n✅ Vidéo traitée avec succès !\n")
    zone_log.see("end")

# --- Interface ---
entete = ctk.CTkFrame(app, fg_color="transparent")
entete.pack(fill="x", padx=20, pady=(15, 0))
ctk.CTkLabel(entete, text="Trieur Audio/Sous-titres", font=("", 18, "bold")).pack(side="left")
ctk.CTkButton(entete, text="⚙", width=40, command=ouvrir_parametres).pack(side="right")

cadre_selection = ctk.CTkFrame(app, fg_color="transparent")
cadre_selection.pack(pady=15)
ctk.CTkButton(cadre_selection, text="📁 Dossier", command=choisir_dossier, width=150).pack(side="left", padx=5)
ctk.CTkButton(cadre_selection, text="🎬 Fichier(s)", command=choisir_fichiers, width=150).pack(side="left", padx=5)

label_selection = ctk.CTkLabel(app, text="Aucune sélection")
label_selection.pack(pady=(0, 10))

ctk.CTkLabel(app, text="Dossier de sortie :").pack(pady=(10, 0))
frame_sortie = ctk.CTkFrame(app, fg_color="transparent")
frame_sortie.pack(pady=5, fill="x", padx=20)
entree_sortie = ctk.CTkEntry(frame_sortie)
entree_sortie.pack(side="left", fill="x", expand=True, padx=(0, 10))
ctk.CTkButton(frame_sortie, text="Parcourir", command=choisir_sortie, width=100).pack(side="left")

ctk.CTkLabel(app, text="Langue audio à garder :").pack(pady=(15, 0))
menu_langue_audio = ctk.CTkOptionMenu(app, values=["Sélectionne d'abord une vidéo"])
menu_langue_audio.pack(pady=5)

case_sous_titres = ctk.CTkCheckBox(app, text="Garder les sous-titres")
case_sous_titres.select()
case_sous_titres.pack(pady=(15, 5))

ctk.CTkLabel(app, text="Langue des sous-titres à garder :").pack(pady=(5, 0))
menu_langue_soustitres = ctk.CTkOptionMenu(app, values=["Sélectionne d'abord une vidéo"])
menu_langue_soustitres.pack(pady=5)

ctk.CTkButton(app, text="▶ Lancer le traitement", command=lancer, height=40).pack(pady=15)

zone_log = ctk.CTkTextbox(app, height=140)
zone_log.pack(pady=10, padx=20, fill="both", expand=True)

app.mainloop()
