from flask import Flask, render_template, request, redirect, url_for
import pymysql
import os
from dotenv import load_dotenv

# Charge les variables du fichier .env dans l'environnement
# (DB_HOST, DB_USER, DB_PASSWORD, DB_NAME deviennent accessibles via os.environ)
load_dotenv()

app = Flask(__name__)


def get_db_connection():
    """Ouvre une connexion à la base MySQL en utilisant les identifiants du .env."""
    return pymysql.connect(
        host=os.environ.get('DB_HOST'),
        user=os.environ.get('DB_USER'),
        password=os.environ.get('DB_PASSWORD'),
        database=os.environ.get('DB_NAME'),
        cursorclass=pymysql.cursors.DictCursor  # les résultats reviendront sous forme de dictionnaires
    )


@app.route('/')
def home():
    return "EventEats Pro — le serveur Flask fonctionne."


@app.route('/test-db')
def test_db():
    """Route de test : vérifie que Flask arrive bien à parler à MySQL."""
    try:
        connexion = get_db_connection()
        with connexion.cursor() as curseur:
            curseur.execute("SELECT COUNT(*) AS total FROM devis")
            resultat = curseur.fetchone()
        connexion.close()
        return f"Connexion MySQL réussie. Nombre de devis actuellement en base : {resultat['total']}"
    except Exception as erreur:
        return f"Erreur de connexion à la base de données : {erreur}", 500


@app.route('/devis', methods=['GET', 'POST'])
def devis():
    if request.method == 'POST':
        # request.form contient toutes les données envoyées par le formulaire HTML,
        # accessibles par le "name" de chaque champ (ex: name="nom" -> request.form['nom'])
        nom = request.form['nom']
        telephone = request.form['telephone']
        date_evenement = request.form.get('date_evenement') or None
        type_evenement = request.form.get('type_evenement')
        nombre_invites = request.form.get('nombre_invites') or None
        adresse = request.form.get('adresse')
        message = request.form.get('message')

        connexion = get_db_connection()
        with connexion.cursor() as curseur:
            curseur.execute(
                """
                INSERT INTO devis (nom, telephone, date_evenement, type_evenement,
                                    nombre_invites, adresse, message)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (nom, telephone, date_evenement, type_evenement,
                 nombre_invites, adresse, message)
            )
            connexion.commit()  # valide définitivement l'insertion dans la base
            nouveau_id = curseur.lastrowid  # récupère l'id auto-généré de la ligne insérée
        connexion.close()

        return render_template('devis.html', success=True, new_id=nouveau_id)

    return render_template('devis.html', success=False)


@app.route('/admin/devis')
def liste_devis():
    connexion = get_db_connection()
    with connexion.cursor() as curseur:
        curseur.execute("SELECT * FROM devis ORDER BY date_creation DESC")
        tous_les_devis = curseur.fetchall()
    connexion.close()
    return render_template('liste.html', devis=tous_les_devis)


@app.route('/admin/devis/<int:devis_id>/modifier', methods=['GET', 'POST'])
def modifier_devis(devis_id):
    connexion = get_db_connection()

    if request.method == 'POST':
        # On récupère les nouvelles valeurs envoyées par le formulaire de modification
        nom = request.form['nom']
        telephone = request.form['telephone']
        date_evenement = request.form.get('date_evenement') or None
        type_evenement = request.form.get('type_evenement')
        nombre_invites = request.form.get('nombre_invites') or None
        adresse = request.form.get('adresse')
        message = request.form.get('message')

        with connexion.cursor() as curseur:
            curseur.execute(
                """
                UPDATE devis
                SET nom = %s, telephone = %s, date_evenement = %s, type_evenement = %s,
                    nombre_invites = %s, adresse = %s, message = %s
                WHERE id = %s
                """,
                (nom, telephone, date_evenement, type_evenement,
                 nombre_invites, adresse, message, devis_id)
            )
            connexion.commit()
        connexion.close()
        return redirect(url_for('liste_devis'))

    # Méthode GET : on affiche le formulaire pré-rempli avec les données actuelles
    with connexion.cursor() as curseur:
        curseur.execute("SELECT * FROM devis WHERE id = %s", (devis_id,))
        devis_actuel = curseur.fetchone()
    connexion.close()

    if devis_actuel is None:
        return "Devis introuvable.", 404

    return render_template('modifier.html', devis=devis_actuel)


@app.route('/admin/devis/<int:devis_id>/supprimer', methods=['POST'])
def supprimer_devis(devis_id):
    connexion = get_db_connection()
    with connexion.cursor() as curseur:
        curseur.execute("DELETE FROM devis WHERE id = %s", (devis_id,))
        connexion.commit()
    connexion.close()
    return redirect(url_for('liste_devis'))


if __name__ == '__main__':
    app.run(debug=True)
