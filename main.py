import httpx
import json
import os
import ast
import operator
import random
import base64
from difflib import SequenceMatcher
from openai import OpenAI


# =========================================
# EINSTELLUNGEN
# =========================================

DATEI = "training.json"

BASE_URL = "https://api.searlo.tech/api/v1/search/web"

# Dein Suchlimit bleibt 20
SUCH_LIMIT = 20


# =========================================
# API-KEYS LADEN
# =========================================

try:
    from config import SEARLO_API_KEY, OPENAI_API_KEY

except ImportError:
    print("FEHLER: config.py wurde nicht gefunden.")
    print("Erstelle eine Datei namens config.py.")
    input("Enter druecken...")
    exit()


# =========================================
# OPENAI STARTEN
# =========================================

client = OpenAI(
    api_key=OPENAI_API_KEY
)


# =========================================
# TEXT NORMALISIEREN
# =========================================

def norm(text):
    return str(text).strip().lower()


# =========================================
# AENLICHKEIT
# =========================================

def aehnlich(a, b):

    return SequenceMatcher(
        None,
        norm(a),
        norm(b)
    ).ratio()


# =========================================
# SICHER RECHNEN
# =========================================

def rechne(text):

    text = text.replace(" ", "")
    text = text.replace(",", ".")
    text = text.replace("x", "*")
    text = text.replace("X", "*")
    text = text.replace(":", "/")

    erlaubte_operatoren = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.USub: operator.neg
    }

    try:

        baum = ast.parse(
            text,
            mode="eval"
        )

        def berechne(knoten):

            if isinstance(knoten, ast.Constant):

                if isinstance(
                    knoten.value,
                    (int, float)
                ):
                    return knoten.value

                raise ValueError

            if isinstance(knoten, ast.BinOp):

                operator_typ = type(knoten.op)

                if operator_typ not in erlaubte_operatoren:
                    raise ValueError

                links = berechne(
                    knoten.left
                )

                rechts = berechne(
                    knoten.right
                )

                return erlaubte_operatoren[
                    operator_typ
                ](
                    links,
                    rechts
                )

            if isinstance(knoten, ast.UnaryOp):

                if isinstance(
                    knoten.op,
                    ast.USub
                ):
                    return -berechne(
                        knoten.operand
                    )

            raise ValueError

        ergebnis = berechne(
            baum.body
        )

        if (
            isinstance(ergebnis, float)
            and ergebnis.is_integer()
        ):
            ergebnis = int(ergebnis)

        return ergebnis

    except Exception:
        return None


# =========================================
# BILD GENERIEREN
# =========================================

def generiere_bild(beschreibung):

    try:

        print()
        print("KM AI: Ich erstelle dein Bild...")
        print()

        ergebnis = client.images.generate(
            model="gpt-image-1",
            prompt=beschreibung,
            size="1024x1024"
        )

        bild_daten = base64.b64decode(
            ergebnis.data[0].b64_json
        )

        os.makedirs(
            "bilder",
            exist_ok=True
        )

        nummer = 1

        while os.path.exists(
            f"bilder/bild_{nummer}.png"
        ):
            nummer += 1

        dateiname = (
            f"bilder/bild_{nummer}.png"
        )

        with open(
            dateiname,
            "wb"
        ) as datei:

            datei.write(
                bild_daten
            )

        print(
            "KM AI: Bild erfolgreich erstellt."
        )

        print(
            "Gespeichert als:"
        )

        print(
            dateiname
        )

    except Exception as e:

        print()
        print(
            "KM AI: Fehler beim Erstellen des Bildes:"
        )

        print(
            str(e)
        )


# =========================================
# FREUNDLICHE ANTWORTEN
# =========================================

def unterhaltung(frage):

    antworten = {

        "hallo":
        "Hallo! Schoen, dass du da bist. Wie kann ich dir helfen?",

        "hi":
        "Hallo! Was moechtest du wissen oder lernen?",

        "hey":
        "Hey! Wie kann ich dir helfen?",

        "wie geht es dir":
        "Mir geht es gut, danke! Wie kann ich dir helfen?",

        "wer bist du":
        "Ich bin KM AI. Ich kann Fragen beantworten, Informationen suchen, rechnen und Bilder erstellen.",

        "wie heisst du":
        "Ich heisse KM AI.",

        "was ist dein name":
        "Mein Name ist KM AI.",

        "was kannst du":
        "Ich kann Fragen beantworten, im Internet suchen, rechnen, beim Lernen helfen und Bilder erstellen.",

        "danke":
        "Sehr gerne! Ich helfe dir gerne.",

        "danke schön":
        "Sehr gerne!",

        "dankeschön":
        "Sehr gerne!",

        "tschüss":
        "Tschuess! Bis bald.",

        "tschuss":
        "Tschuess! Bis bald."
    }

    return antworten.get(
        norm(frage)
    )


# =========================================
# EINFACHES WISSEN
# =========================================

def allgemeines_wissen(frage):

    wissen = {

        "wie viele tage hat eine woche":
        "Eine Woche hat sieben Tage.",

        "wie viele monate hat ein jahr":
        "Ein Jahr hat zwoelf Monate.",

        "wie viele stunden hat ein tag":
        "Ein Tag hat 24 Stunden.",

        "wie viele minuten hat eine stunde":
        "Eine Stunde hat 60 Minuten.",

        "wie viele sekunden hat eine minute":
        "Eine Minute hat 60 Sekunden.",

        "was ist python":
        "Python ist eine Programmiersprache. Damit kann man Programme, Spiele, Webseiten und KI-Anwendungen erstellen.",

        "was ist eine ki":
        "KI bedeutet kuenstliche Intelligenz. Je nach Programm kann eine KI Informationen verarbeiten und bei Aufgaben helfen."
    }

    return wissen.get(
        norm(frage)
    )


# =========================================
# TRAININGSDATEN LADEN
# =========================================

def lade_daten():

    if not os.path.exists(DATEI):
        return []

    try:

        with open(
            DATEI,
            "r",
            encoding="utf-8"
        ) as datei:

            daten = json.load(
                datei
            )

        if isinstance(
            daten,
            list
        ):
            return daten

    except Exception:

        print(
            "Hinweis: training.json ist leer oder fehlerhaft."
        )

    return []


# =========================================
# TRAININGSDATEN SPEICHERN
# =========================================

def speichere_daten(daten):

    try:

        with open(
            DATEI,
            "w",
            encoding="utf-8"
        ) as datei:

            json.dump(
                daten,
                datei,
                ensure_ascii=False,
                indent=4
            )

        return True

    except Exception as e:

        print(
            "Fehler beim Speichern:"
        )

        print(
            str(e)
        )

        return False


# =========================================
# GELERNTE ANTWORT SUCHEN
# =========================================

def finde_antwort(frage, daten):

    beste_antwort = None
    bester_wert = 0

    for eintrag in daten:

        if not isinstance(
            eintrag,
            dict
        ):
            continue

        alte_frage = eintrag.get(
            "frage"
        )

        antwort = eintrag.get(
            "antwort"
        )

        if not alte_frage:
            continue

        if not antwort:
            continue

        wert = aehnlich(
            frage,
            alte_frage
        )

        if wert > bester_wert:

            bester_wert = wert
            beste_antwort = antwort

    if bester_wert >= 0.82:
        return beste_antwort

    return None


# =========================================
# NEUE ANTWORT LERNEN
# =========================================

def lernen(frage, antwort, daten):

    neuer_eintrag = {

        "frage": frage,

        "antwort": antwort
    }

    daten.append(
        neuer_eintrag
    )

    speichere_daten(
        daten
    )


# =========================================
# SEARLO WEBSUCHE
# =========================================

def websuche(frage):

    try:

        response = httpx.get(

            BASE_URL,

            params={
                "q": frage,
                "limit": SUCH_LIMIT
            },

            headers={
                "x-api-key": SEARLO_API_KEY,
                "Accept": "application/json"
            },

            timeout=30
        )

        response.raise_for_status()

        return response.json()

    except Exception as e:

        return {
            "error": str(e)
        }


# =========================================
# SUCHERGEBNISSE HOLEN
# =========================================

def hole_ergebnisse(ergebnis):

    if not isinstance(
        ergebnis,
        dict
    ):
        return []

    moegliche_felder = [

        "results",

        "organic",

        "data",

        "web"
    ]

    for feld in moegliche_felder:

        ergebnisse = ergebnis.get(
            feld
        )

        if isinstance(
            ergebnisse,
            list
        ):
            return ergebnisse

    return []


# =========================================
# SUCHERGEBNISSE BEWERTEN
# =========================================

def bewerte_ergebnis(frage, item):

    titel = str(
        item.get("title", "")
    )

    text = str(

        item.get("snippet")

        or item.get("description")

        or item.get("text")

        or ""
    )

    gesamter_text = norm(
        titel + " " + text
    )

    punkte = 0

    frage_woerter = norm(
        frage
    ).split()

    for wort in frage_woerter:

        if len(wort) > 2:

            if wort in gesamter_text:
                punkte += 1

    punkte += min(
        len(text) / 300,
        2
    )

    return punkte


# =========================================
# BESTE SUCHERGEBNISSE AUSWAEHLEN
# =========================================

def waehle_beste_ergebnisse(
    frage,
    ergebnisse
):

    bewertete_ergebnisse = []

    for item in ergebnisse:

        if not isinstance(
            item,
            dict
        ):
            continue

        text = (

            item.get("snippet")

            or item.get("description")

            or item.get("text")

            or ""
        )

        if len(str(text)) < 20:
            continue

        punkte = bewerte_ergebnis(
            frage,
            item
        )

        bewertete_ergebnisse.append({

            "item": item,

            "punkte": punkte
        })

    bewertete_ergebnisse.sort(

        key=lambda x: x["punkte"],

        reverse=True
    )

    beste_ergebnisse = []

    for eintrag in bewertete_ergebnisse:

        item = eintrag["item"]

        text = str(

            item.get("snippet")

            or item.get("description")

            or item.get("text")

            or ""
        )

        doppelt = False

        for vorhandenes_item in beste_ergebnisse:

            vorhandener_text = str(

                vorhandenes_item.get("snippet")

                or vorhandenes_item.get("description")

                or vorhandenes_item.get("text")

                or ""
            )

            if aehnlich(
                text,
                vorhandener_text
            ) > 0.85:

                doppelt = True

                break

        if not doppelt:

            beste_ergebnisse.append(
                item
            )

    return beste_ergebnisse


# =========================================
# TEXT IN SAETZE TEILEN
# =========================================

def saetze_aus_text(text):

    text = str(text)

    text = text.replace(
        "\n",
        " "
    )

    teile = text.split(
        "."
    )

    saetze = []

    for teil in teile:

        teil = teil.strip()

        if len(teil) >= 25:

            saetze.append(
                teil + "."
            )

    return saetze


# =========================================
# ANTWORT AUS VIELEN QUELLEN ERSTELLEN
# =========================================

def erstelle_gute_antwort(
    frage,
    ergebnisse
):

    informationen = []

    for item in ergebnisse:

        text = (

            item.get("snippet")

            or item.get("description")

            or item.get("text")

            or ""
        )

        saetze = saetze_aus_text(
            text
        )

        for satz in saetze:

            doppelt = False

            for vorhandene_info in informationen:

                if aehnlich(
                    satz,
                    vorhandene_info
                ) > 0.85:

                    doppelt = True

                    break

            if not doppelt:

                informationen.append(
                    satz
                )

    if not informationen:

        return None

    informationen = informationen[:8]

    antwort = "Gerne! "

    for information in informationen:

        antwort += (
            information
            + " "
        )

    return antwort.strip()


# =========================================
# NUR 2 QUELLEN ANZEIGEN
# =========================================

def zeige_quellen(ergebnisse):

    print()
    print("Quellen:")

    anzahl = 0

    for item in ergebnisse:

        if anzahl >= 2:
            break

        if not isinstance(
            item,
            dict
        ):
            continue

        titel = item.get(
            "title"
        ) or "Unbekannte Quelle"

        link = (

            item.get("url")

            or item.get("link")

            or ""
        )

        if link:

            anzahl += 1

            print()

            print(
                str(anzahl)
                + ". "
                + str(titel)
            )

            print(
                "   "
                + str(link)
            )


# =========================================
# INTERNETFRAGE BEANTWORTEN
# =========================================

def frage_im_internet(frage):

    print()
    print(
        "KM AI: Ich suche nach Informationen..."
    )

    ergebnis = websuche(
        frage
    )

    if "error" in ergebnis:

        print()
        print(
            "KM AI: Fehler bei der Websuche:"
        )

        print(
            ergebnis["error"]
        )

        return None

    alle_ergebnisse = hole_ergebnisse(
        ergebnis
    )

    if not alle_ergebnisse:

        print()
        print(
            "KM AI: Ich habe keine Informationen gefunden."
        )

        return None

    beste_ergebnisse = waehle_beste_ergebnisse(

        frage,

        alle_ergebnisse
    )

    if not beste_ergebnisse:

        print()
        print(
            "KM AI: Ich habe keine guten Informationen gefunden."
        )

        return None

    antwort = erstelle_gute_antwort(

        frage,

        beste_ergebnisse
    )

    if not antwort:

        print()
        print(
            "KM AI: Ich konnte keine gute Antwort erstellen."
        )

        return None

    print()

    print("KM AI:")

    print()

    print(antwort)

    zeige_quellen(
        beste_ergebnisse
    )

    return antwort


# =========================================
# MATHE-LERNMODUS
# =========================================

def starte_mathe_lernen():

    print()
    print(
        "KM AI: Sehr gerne! Ich helfe dir beim Mathelernen."
    )

    print()

    print("1. Plus")
    print("2. Minus")
    print("3. Mal")

    wahl = input(
        "\nDu: "
    ).strip()

    if wahl == "1":

        thema = "plus"

        print(
            "\nKM AI: Beim Addieren werden Zahlen zusammengezaehlt."
        )

    elif wahl == "2":

        thema = "minus"

        print(
            "\nKM AI: Beim Subtrahieren wird eine Zahl von einer anderen abgezogen."
        )

    elif wahl == "3":

        thema = "mal"

        print(
            "\nKM AI: Beim Multiplizieren werden Zahlen miteinander vervielfacht."
        )

    else:

        print(
            "\nKM AI: Ungueltige Auswahl."
        )

        return

    print()

    print(
        "Schreibe 'ende', wenn du aufhoeren moechtest."
    )

    letzte_aufgabe = ""

    while True:

        while True:

            a = random.randint(
                1,
                20
            )

            b = random.randint(
                1,
                20
            )

            if thema == "plus":

                aufgabe = (
                    str(a)
                    + " + "
                    + str(b)
                )

                loesung = a + b

            elif thema == "minus":

                if b > a:
                    a, b = b, a

                aufgabe = (
                    str(a)
                    + " - "
                    + str(b)
                )

                loesung = a - b

            else:

                a = random.randint(
                    1,
                    10
                )

                b = random.randint(
                    1,
                    10
                )

                aufgabe = (
                    str(a)
                    + " * "
                    + str(b)
                )

                loesung = a * b

            if aufgabe != letzte_aufgabe:

                letzte_aufgabe = aufgabe

                break

        antwort = input(

            "\nKM AI: "
            + aufgabe
            + " = "

        ).strip()

        if norm(antwort) == "ende":

            print(
                "\nKM AI: Gut gemacht!"
            )

            return

        try:

            if int(antwort) == loesung:

                print(
                    "KM AI: Richtig! Sehr gut!"
                )

            else:

                print(
                    "KM AI: Leider nicht richtig. Die Antwort ist "
                    + str(loesung)
                    + "."
                )

        except ValueError:

            print(
                "KM AI: Bitte gib eine Zahl ein."
            )


# =========================================
# HAUPTPROGRAMM
# =========================================

def main():

    daten = lade_daten()

    print()
    print("======================================")
    print("KM AI gestartet")
    print("======================================")
    print()

    print("Ich kann:")
    print("- Fragen beantworten")
    print("- Im Internet suchen")
    print("- Rechnen")
    print("- Mathe erklaeren")
    print("- Bilder erstellen")

    print()

    print("Beispiele:")
    print("Was ist Minecraft?")
    print("1 + 1")
    print("Ich will Mathe lernen")
    print("Bild eine Katze im Weltraum")

    print()

    print("Schreibe 'ende' zum Beenden.")

    print()

    while True:

        frage = input(
            "Du: "
        ).strip()

        if not frage:
            continue

        # -------------------------------------
        # BEENDEN
        # -------------------------------------

        if norm(frage) == "ende":

            print()

            print(
                "KM AI: Tschuess! Bis bald."
            )

            break

        # -------------------------------------
        # BILD GENERIEREN
        # -------------------------------------

        if norm(frage).startswith("bild "):

            beschreibung = frage[5:].strip()

            if beschreibung:

                generiere_bild(
                    beschreibung
                )

            else:

                print(
                    "KM AI: Bitte beschreibe das Bild."
                )

            continue

        # -------------------------------------
        # MATHE LERNEN
        # -------------------------------------

        if (
            "mathe lernen" in norm(frage)
            or
            "mathematik lernen" in norm(frage)
        ):

            starte_mathe_lernen()

            continue

        # -------------------------------------
        # RECHNEN
        # -------------------------------------

        ergebnis = rechne(
            frage
        )

        if ergebnis is not None:

            print()

            print(
                "KM AI: Das Ergebnis ist "
                + str(ergebnis)
                + "."
            )

            continue

        # -------------------------------------
        # NORMALE UNTERHALTUNG
        # -------------------------------------

        antwort = unterhaltung(
            frage
        )

        if antwort:

            print()

            print(
                "KM AI: "
                + antwort
            )

            continue

        # -------------------------------------
        # EINFACHES WISSEN
        # -------------------------------------

        antwort = allgemeines_wissen(
            frage
        )

        if antwort:

            print()

            print(
                "KM AI: "
                + antwort
            )

            continue

        # -------------------------------------
        # GELERNTE ANTWORTEN
        # -------------------------------------

        antwort = finde_antwort(

            frage,

            daten
        )

        if antwort:

            print()

            print(
                "KM AI: "
                + antwort
            )

            continue

        # -------------------------------------
        # INTERNET
        # -------------------------------------

        antwort = frage_im_internet(
            frage
        )

        # -------------------------------------
        # ANTWORT LERNEN
        # -------------------------------------

        if antwort:

            speichern = input(

                "\nSoll ich diese Antwort speichern? "
                "(ja/nein): "

            ).strip().lower()

            if speichern == "ja":

                lernen(

                    frage,

                    antwort,

                    daten
                )

                print(
                    "\nKM AI: Antwort wurde gespeichert."
                )


# =========================================
# NUR STARTEN, WENN MAIN.PY
# DIREKT AUSGEFUEHRT WIRD
# =========================================

if __name__ == "__main__":
    main()
