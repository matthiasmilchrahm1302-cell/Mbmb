from flask import Flask, request, jsonify
from flask_cors import CORS

from main import (
    unterhaltung,
    allgemeines_wissen,
    rechne,
    finde_antwort,
    lade_daten,
    websuche,
    hole_ergebnisse,
    waehle_beste_ergebnisse,
    erstelle_gute_antwort
)

app = Flask(__name__)
CORS(app)

daten = lade_daten()


@app.route("/")
def startseite():
    return "KM AI Server läuft!"


@app.route("/chat", methods=["POST"])
def chat():

    try:
        eingabe = request.get_json()

        if not eingabe:
            return jsonify({
                "antwort": "Keine Frage erhalten."
            })

        frage = str(
            eingabe.get("frage", "")
        ).strip()

        if not frage:
            return jsonify({
                "antwort": "Bitte schreibe eine Frage."
            })


        # ==============================
        # BEENDEN
        # ==============================

        if frage.lower() == "ende":
            return jsonify({
                "antwort": "Bis bald!"
            })


        # ==============================
        # BILD
        # ==============================

        if frage.lower().startswith("bild "):
            return jsonify({
                "antwort":
                    "Die Bildfunktion bauen wir als eigenen Schritt ein."
            })


        # ==============================
        # RECHNEN
        # ==============================

        ergebnis = rechne(frage)

        if ergebnis is not None:

            return jsonify({
                "antwort":
                    "Das Ergebnis ist "
                    + str(ergebnis)
                    + "."
            })


        # ==============================
        # UNTERHALTUNG
        # ==============================

        antwort = unterhaltung(frage)

        if antwort:

            return jsonify({
                "antwort": antwort
            })


        # ==============================
        # EINFACHES WISSEN
        # ==============================

        antwort = allgemeines_wissen(frage)

        if antwort:

            return jsonify({
                "antwort": antwort
            })


        # ==============================
        # GELERNTE ANTWORT
        # ==============================

        antwort = finde_antwort(
            frage,
            daten
        )

        if antwort:

            return jsonify({
                "antwort": antwort
            })


        # ==============================
        # INTERNET
        # ==============================

        suchergebnis = websuche(frage)

        if not isinstance(
            suchergebnis,
            dict
        ):

            return jsonify({
                "antwort":
                    "Die Websuche konnte nicht ausgeführt werden."
            })


        if "error" in suchergebnis:

            return jsonify({
                "antwort":
                    "Bei der Websuche ist ein Fehler aufgetreten."
            })


        alle_ergebnisse = hole_ergebnisse(
            suchergebnis
        )


        if not alle_ergebnisse:

            return jsonify({
                "antwort":
                    "Ich habe keine Informationen gefunden."
            })


        beste_ergebnisse = waehle_beste_ergebnisse(
            frage,
            alle_ergebnisse
        )


        if not beste_ergebnisse:

            return jsonify({
                "antwort":
                    "Ich habe keine guten Informationen gefunden."
            })


        antwort = erstelle_gute_antwort(
            frage,
            beste_ergebnisse
        )


        if not antwort:

            return jsonify({
                "antwort":
                    "Ich konnte keine Antwort erstellen."
            })


        # ==============================
        # QUELLEN
        # ==============================

        quellen = []

        for item in beste_ergebnisse:

            if len(quellen) >= 2:
                break

            titel = (
                item.get("title")
                or "Unbekannte Quelle"
            )

            link = (
                item.get("url")
                or item.get("link")
                or ""
            )

            if link:

                quellen.append({
                    "titel": str(titel),
                    "link": str(link)
                })


        return jsonify({
            "antwort": antwort,
            "quellen": quellen
        })


    except Exception as e:

        print(
            "SERVER-FEHLER:",
            str(e)
        )

        return jsonify({
            "antwort":
                "KM AI hat einen Serverfehler."
        }), 500


if __name__ == "__main__":

    import os

    port = int(
        os.environ.get(
            "PORT",
            5000
        )
    )

    app.run(
        host="0.0.0.0",
        port=port,
        debug=True
    )
