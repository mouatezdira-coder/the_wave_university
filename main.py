from flask import Flask, render_template, request, redirect, session, url_for, flash
import os
import db
from datetime import timedelta, datetime
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.secret_key = 'projet_thewave_secret' 
app.permanent_session_lifetime = timedelta(minutes=60)

def execute_query(query, params=(), fetch_one=False):

    conn = db.connect()
    cur = conn.cursor()
    try:
        cur.execute(query, params)
        is_select = query.strip().upper().startswith('SELECT')
        has_returning = 'RETURNING' in query.upper()
        if is_select:
            result = cur.fetchone() if fetch_one else cur.fetchall()
        else:
            if has_returning:
                result = cur.fetchone() if fetch_one else cur.fetchall()
            else:
                result = None
            conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"SQL Error: {e}")
        if query.strip().upper().startswith('SELECT'):
            result = None if fetch_one else []
        else:
            result = None
    finally:
        cur.close()
        conn.close()

    if query.strip().upper().startswith('SELECT') and not fetch_one:
        return result if result is not None else []
    return result


def hash_password(password: str) -> str:
    """Return a secure hash for the given password."""
    return generate_password_hash(password)


def verify_password(stored: str, provided: str) -> bool:
    """Verify a provided password against a stored hash.

    Supports legacy plain-text passwords by accepting an exact match and recommending an upgrade.
    """
    if not stored:
        return False

    if check_password_hash(stored, provided):
        return True

    return stored == provided


@app.route('/')
def home():

    sql_top = """
        SELECT m.idm, m.titre, g.nomg, COUNT(h.idh) as ecoutes
        FROM morceau m
        JOIN record_historique h ON m.idm = h.idm
        JOIN groupe g ON m.idg = g.idg
        WHERE h.historique >= NOW() - INTERVAL '7 days'
        GROUP BY m.idm, m.titre, g.nomg
        ORDER BY ecoutes DESC LIMIT 5;
    """

    sql_groups = """
        SELECT g.idg, g.nomg, COUNT(s.idu) as followers
        FROM groupe g
        LEFT JOIN suit s ON g.idg = s.idg
        GROUP BY g.idg, g.nomg
        ORDER BY followers DESC LIMIT 5;
    """

    sql_albums = "SELECT idal, titre, date_pari FROM album ORDER BY date_pari DESC LIMIT 5;"
    
    return render_template('home.html', 
                           tracks=execute_query(sql_top), 
                           groups=execute_query(sql_groups), 
                           albums=execute_query(sql_albums))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        pseudo = request.form['pseudo']
        mdp = request.form['password']

        user = execute_query("SELECT idu, pseudo, mdp FROM utilisateur WHERE pseudo = %s", (pseudo,), fetch_one=True)
        if user and verify_password(user[2], mdp):
            session['user_id'] = user[0]
            session['pseudo'] = user[1]

            if user[2] == mdp:
                execute_query("UPDATE utilisateur SET mdp = %s WHERE idu = %s", (hash_password(mdp), user[0]))

            return redirect(url_for('home'))
        flash("Identifiants incorrects", "error")
    return render_template('login.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        try:
            sql = "INSERT INTO utilisateur (pseudo, email, mdp, date_IN) VALUES (%s, %s, %s, CURRENT_DATE)"
            execute_query(sql, (request.form['pseudo'], request.form['email'], hash_password(request.form['password'])))
            flash("Compte créé ! Connectez-vous.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            # Common causes: unique constraint violation, or mdp column too short for hashed password.
            print(f"Signup error: {e}")
            flash("Ce pseudo ou email existe déjà.", "error")
    return render_template('signup.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))


@app.route('/search')
def search():
    q = request.args.get('q', '')
    results = {'tracks': [], 'albums': [], 'groups': [], 'playlists': []}
    
    if q:
        term = f"%{q}%"
        
        sql_tracks = """
            SELECT DISTINCT m.idm, m.titre, g.nomg 
            FROM morceau m
            JOIN groupe g ON m.idg = g.idg
            WHERE m.titre ILIKE %s 
               OR g.nomg ILIKE %s 
               OR g.genre ILIKE %s 
               OR m.parole ILIKE %s
        """
        results['tracks'] = execute_query(sql_tracks, (term, term, term, term))
        
        sql_albums = """
            SELECT DISTINCT a.idal, a.titre, g.nomg
            FROM album a
            JOIN morceau m ON a.idal = m.idal
            JOIN groupe g ON m.idg = g.idg
            WHERE a.titre ILIKE %s 
               OR g.nomg ILIKE %s
        """
        results['albums'] = execute_query(sql_albums, (term, term))
        
        sql_groups = """
            SELECT idg, nomg, genre 
            FROM groupe 
            WHERE nomg ILIKE %s 
               OR genre ILIKE %s
        """
        results['groups'] = execute_query(sql_groups, (term, term))

        sql_playlists = """
            SELECT p.idp, p.titre, u.pseudo
            FROM playlist p
            JOIN utilisateur u ON p.idu = u.idu
            WHERE (p.titre ILIKE %s OR p.description ILIKE %s)
              AND p.statut = 'public'
        """
        results['playlists'] = execute_query(sql_playlists, (term, term))
            
    return render_template('search.html', results=results, q=q)



from datetime import date  

@app.route('/group/<int:id_groupe>')
def group_page(id_groupe):
    info = execute_query("SELECT nomg, genre, nationG, date_crea FROM groupe WHERE idg=%s", (id_groupe,), fetch_one=True)
    
    if not info:
        return "Groupe introuvable", 404

    sql_members = """
        SELECT a.prenom, a.nom, c.role, c.date_entree, c.date_sortie, a.idart 
        FROM contrat c 
        JOIN artist a ON c.idart = a.idart 
        WHERE c.idg = %s
        ORDER BY c.date_sortie DESC
    """
    members = execute_query(sql_members, (id_groupe,))

    albums = execute_query("""
        SELECT DISTINCT a.idal, a.titre, a.date_pari 
        FROM album a 
        JOIN morceau m ON a.idal=m.idal 
        WHERE m.idg=%s
        ORDER BY a.date_pari DESC
    """, (id_groupe,))

    tracks = execute_query("""
        SELECT idm, titre, duree 
        FROM morceau 
        WHERE idg=%s 
        ORDER BY titre ASC
    """, (id_groupe,))

    followers_data = execute_query("SELECT COUNT(*) FROM suit WHERE idg=%s", (id_groupe,), fetch_one=True)
    followers = followers_data[0] if followers_data else 0
    is_following = False
    if 'user_id' in session:
        check = execute_query("SELECT 1 FROM suit WHERE idu=%s AND idg=%s", (session['user_id'], id_groupe), fetch_one=True)
        if check: is_following = True
    return render_template('group.html', group=info, members=members, albums=albums, tracks=tracks, followers=followers, today=date.today(),is_following=is_following)

@app.route('/history')
def history():
    if 'user_id' not in session: return redirect(url_for('login'))
    sql = "SELECT m.titre, g.nomg, h.historique, m.idm, g.idg FROM record_historique h JOIN morceau m ON h.idm=m.idm JOIN groupe g ON m.idg=g.idg WHERE h.idu=%s ORDER BY h.historique DESC LIMIT 50"
    hist = execute_query(sql, (session['user_id'],))
    return render_template('history.html', history=hist if hist is not None else [])


@app.route('/create_playlist', methods=['GET', 'POST'])
def create_playlist():
    if 'user_id' not in session: return redirect(url_for('login'))
    if request.method == 'POST':
        titre = request.form.get('titre')
        description = request.form.get('description', '')
        statut = request.form.get('statut', 'public')
        execute_query("INSERT INTO playlist (titre, description, statut, idu) VALUES (%s, %s, %s, %s)", 
                  (titre, description, statut, session['user_id']))
        return redirect(url_for('profile'))
    return render_template('create_playlist.html')

@app.route('/playlist/<int:id_playlist>')
def playlist_detail(id_playlist):
    pl = execute_query("SELECT idp, titre, description, statut FROM playlist WHERE idp=%s", (id_playlist,), fetch_one=True)
    if not pl:
        return "Playlist introuvable", 404
    tracks = execute_query("SELECT m.idm, m.titre, g.nomg, m.duree FROM possede p JOIN morceau m ON p.idm=m.idm JOIN groupe g ON m.idg=g.idg WHERE p.idp=%s ORDER BY p.positionp", (id_playlist,))
    return render_template('playlist.html', playlist=pl, tracks=tracks)

@app.route('/add_to_playlist', methods=['POST'])
def add_to_playlist():
    if 'user_id' not in session: return redirect(url_for('login'))
    pid = request.form.get('playlist_id')
    mid = request.form.get('track_id')
    try:
        pid = int(pid)
        mid = int(mid)
    except Exception:
        flash("Invalid input.", "error")
        return redirect(url_for('home'))
    try:
        pos_data = execute_query("SELECT COALESCE(MAX(positionp), 0)+1 FROM possede WHERE idp=%s", (pid,), fetch_one=True)
        pos = pos_data[0] if pos_data else 1
        execute_query("INSERT INTO possede (idp, idm, positionp) VALUES (%s, %s, %s)", (pid, mid, pos))
        flash("Ajouté !", "success")
    except: flash("Déjà présent.", "error")
    return redirect(url_for('track_page', id_morceau=mid))

@app.route('/discover')
def discover():
    if 'user_id' not in session: return redirect(url_for('login'))
    uid = session['user_id']
    

    sql_artists = """
        SELECT DISTINCT m.idm, m.titre, g.nomg, m.duree
        FROM morceau m
        JOIN groupe g ON m.idg = g.idg
        WHERE m.idg IN (
            -- Subquery: My Top 3 Groups
            SELECT m2.idg 
            FROM record_historique h 
            JOIN morceau m2 ON h.idm = m2.idm 
            WHERE h.idu = %s 
            GROUP BY m2.idg 
            ORDER BY COUNT(*) DESC LIMIT 3
        )
        AND m.idm NOT IN (SELECT idm FROM record_historique WHERE idu = %s)
        LIMIT 10;
    """
    suggestions_artist = execute_query(sql_artists, (uid, uid))


    sql_playlists = """
        SELECT p.idp, p.titre, u.pseudo, COUNT(pos.idm) as matches
        FROM playlist p
        JOIN possede pos ON p.idp = pos.idp
        JOIN utilisateur u ON p.idu = u.idu
        WHERE pos.idm IN (SELECT idm FROM record_historique WHERE idu = %s)
        AND p.statut = 'public'
        AND p.idu != %s
        GROUP BY p.idp, p.titre, u.pseudo
        ORDER BY matches DESC
        LIMIT 5;
    """
    suggestions_playlist = execute_query(sql_playlists, (uid, uid))


    sql_collab = """
        SELECT g.idg, g.nomg, COUNT(s.idu) as popularity
        FROM suit s 
        JOIN groupe g ON s.idg = g.idg
        WHERE s.idu IN (
            -- Find users who listened to the same tracks as me
            SELECT DISTINCT h2.idu
            FROM record_historique h1
            JOIN record_historique h2 ON h1.idm = h2.idm
            WHERE h1.idu = %s AND h2.idu != %s
        )
        AND s.idg NOT IN (SELECT idg FROM suit WHERE idu = %s) -- Groups I don't follow yet
        GROUP BY g.idg, g.nomg
        ORDER BY popularity DESC
        LIMIT 5;
    """
    suggestions_collab = execute_query(sql_collab, (uid, uid, uid))

    return render_template('discover.html', 
                           by_artist=suggestions_artist, 
                           by_playlist=suggestions_playlist, 
                           by_users=suggestions_collab)

@app.route('/artist/<int:id_artist>')
def artist_page(id_artist):

    sql_info = """
        SELECT nom, prenom, nationA, date_N, date_M 
        FROM artist 
        WHERE idart = %s
    """
    artist = execute_query(sql_info, (id_artist,), fetch_one=True)
    
    if not artist:
        return "Artiste introuvable", 404


    sql_groups = """
        SELECT g.idg, g.nomg, c.role, c.date_entree, c.date_sortie
        FROM contrat c
        JOIN groupe g ON c.idg = g.idg
        WHERE c.idart = %s
        ORDER BY c.date_entree DESC
    """
    groups = execute_query(sql_groups, (id_artist,))


    sql_tracks = """
        SELECT m.idm, m.titre, p.role, g.nomg, g.idg
        FROM participe p
        JOIN morceau m ON p.idm = m.idm
        JOIN groupe g ON m.idg = g.idg
        WHERE p.idart = %s
    """
    participations = execute_query(sql_tracks, (id_artist,))

    return render_template('artist.html', artist=artist, groups=groups, participations=participations)

@app.route('/track/<int:id_morceau>')  
def track_page(id_morceau):           

    sql = """
        SELECT m.idm, m.titre, m.duree, m.parole, m.url, 
               g.nomg, g.idg, 
               a.titre, a.idal, a.description, a.date_pari
        FROM morceau m
        JOIN groupe g ON m.idg = g.idg
        JOIN album a ON m.idal = a.idal
        WHERE m.idm = %s
    """
    track = execute_query(sql, (id_morceau,), fetch_one=True)
    
    if not track:
        return "Morceau introuvable", 404

    play_count_data = execute_query("SELECT COUNT(*) FROM record_historique WHERE idm=%s", (id_morceau,), fetch_one=True)
    play_count = play_count_data[0] if play_count_data else 0

    sql_credits = """
        SELECT ar.prenom, ar.nom, p.role, ar.idart
        FROM participe p
        JOIN artist ar ON p.idart = ar.idart
        WHERE p.idm = %s
    """
    credits = execute_query(sql_credits, (id_morceau,))
    
    playlists = []
    if 'user_id' in session:
        playlists = execute_query("SELECT idp, titre FROM playlist WHERE idu = %s", (session['user_id'],))
        
    return render_template('track.html', track=track, credits=credits, user_playlists=playlists, play_count=play_count)


@app.route('/record_play', methods=['POST'])
def record_play():
    if 'user_id' not in session:
        return ('', 401)

    data = request.get_json() or {}
    track_id = data.get('track_id')
    try:
        track_id = int(track_id)
    except Exception:
        return ('', 400)

    try:
        execute_query("INSERT INTO record_historique (historique, idm, idu) VALUES (NOW(), %s, %s)", (track_id, session['user_id']))
        return ('', 204)
    except Exception as e:
        print(f"Error recording play: {e}")
        return ('', 500)



@app.route('/album/<int:id_album>')    
def album_page(id_album): 
    sql_album = """
        SELECT a.titre, a.description, a.date_pari, g.nomg, g.idg 
        FROM album a 
        JOIN morceau m ON a.idal=m.idal 
        JOIN groupe g ON m.idg=g.idg 
        WHERE a.idal=%s 
        LIMIT 1
    """
    album = execute_query(sql_album, (id_album,), fetch_one=True)
    
    if not album:
        return "Album introuvable", 404

    sql_tracks = """
        SELECT idm, titre, duree, positionA, url 
        FROM morceau 
        WHERE idal = %s 
        ORDER BY positionA ASC
    """
    tracks = execute_query(sql_tracks, (id_album,))

    return render_template('album.html', album=album, tracks=tracks, id_album=id_album)


@app.context_processor
def utility_processor():
    def album_cover(album_id):
        for ext in ('.png', '.jpg', '.jpeg', '.webp'):
            fname = f'covers/cover{album_id}{ext}'
            path = os.path.join(app.static_folder, fname)
            if os.path.exists(path):
                return url_for('static', filename=fname)
        fallback = 'covers/cover1.png'
        if os.path.exists(os.path.join(app.static_folder, fallback)):
            return url_for('static', filename=fallback)
        return url_for('static', filename='style.css')

    def track_cover(track_id):
        for ext in ('.png', '.jpg', '.jpeg', '.webp', '.svg'):
            fname = f'covers/tcover{track_id}{ext}'
            path = os.path.join(app.static_folder, fname)
            if os.path.exists(path):
                return url_for('static', filename=fname)

        for ext in ('.png', '.jpg', '.jpeg', '.webp', '.svg'):
            dfname = f'covers/tcover_default{ext}'
            if os.path.exists(os.path.join(app.static_folder, dfname)):
                return url_for('static', filename=dfname)

        fallback_icon = 'img/music_note.png'
        if os.path.exists(os.path.join(app.static_folder, fallback_icon)):
            return url_for('static', filename=fallback_icon)

        fallback2 = 'covers/cover1.png'
        if os.path.exists(os.path.join(app.static_folder, fallback2)):
            return url_for('static', filename=fallback2)

        return url_for('static', filename='style.css')

    return dict(album_cover=album_cover, track_cover=track_cover)


@app.route('/profile')
def profile():
    if 'user_id' not in session: return redirect(url_for('login'))
    uid = session['user_id']
    
    user = execute_query("SELECT pseudo, email, date_in FROM utilisateur WHERE idu=%s", (uid,), fetch_one=True)
    
    sql_top = """
        SELECT m.titre, g.nomg, COUNT(h.idm) as c, m.idm 
        FROM record_historique h 
        JOIN morceau m ON h.idm=m.idm 
        JOIN groupe g ON m.idg=g.idg 
        WHERE h.idu=%s 
        GROUP BY m.idm, m.titre, g.nomg 
        ORDER BY c DESC LIMIT 5
    """
    top_tracks = execute_query(sql_top, (uid,))
    
    sql_hist = """
        SELECT m.titre, g.nomg, h.historique, m.idm 
        FROM record_historique h 
        JOIN morceau m ON h.idm=m.idm 
        JOIN groupe g ON m.idg=g.idg 
        WHERE h.idu=%s 
        ORDER BY h.historique DESC LIMIT 10
    """
    history = execute_query(sql_hist, (uid,))
    
    playlists = execute_query("SELECT idp, titre, statut, description FROM playlist WHERE idu=%s ORDER BY idp DESC", (uid,))
    
    sql_feed_albums = """
        SELECT a.titre, g.nomg, a.date_pari, a.idal
        FROM suit s
        JOIN groupe g ON s.idg = g.idg
        JOIN morceau m ON g.idg = m.idg
        JOIN album a ON m.idal = a.idal
        WHERE s.idu = %s
        GROUP BY a.idal, a.titre, g.nomg, a.date_pari
        ORDER BY a.date_pari DESC LIMIT 5
    """
    feed_albums = execute_query(sql_feed_albums, (uid,))

    sql_feed_friends = """
        SELECT p.titre, u.pseudo, p.idp
        FROM follow f
        JOIN playlist p ON f.idu2 = p.idu
        JOIN utilisateur u ON p.idu = u.idu
        WHERE f.idu = %s AND p.statut = 'public'
        ORDER BY p.idp DESC LIMIT 5
    """
    feed_friends = execute_query(sql_feed_friends, (uid,))

    return render_template('profile.html', user=user, top_tracks=top_tracks, history=history, playlists=playlists, feed_albums=feed_albums, feed_friends=feed_friends)


@app.route('/edit_playlist/<int:id_playlist>', methods=['GET', 'POST'])
def edit_playlist(id_playlist):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    check = execute_query("SELECT idp, titre, description, statut FROM playlist WHERE idp=%s AND idu=%s", (id_playlist, session['user_id']), fetch_one=True)
    if not check:
        flash("Accès refusé ou playlist introuvable.", "error")
        return redirect(url_for('profile'))

    if request.method == 'POST':
        execute_query("UPDATE playlist SET titre=%s, description=%s, statut=%s WHERE idp=%s", 
                      (request.form['titre'], request.form['description'], request.form['statut'], id_playlist))
        flash("Playlist mise à jour !", "success")
        return redirect(url_for('profile'))
    
    tracks = execute_query("""
        SELECT m.idm, m.titre, g.nomg, p.positionp 
        FROM possede p 
        JOIN morceau m ON p.idm=m.idm 
        JOIN groupe g ON m.idg=g.idg 
        WHERE p.idp=%s 
        ORDER BY p.positionp ASC
    """, (id_playlist,))
    
    return render_template('edit_playlist.html', playlist=check, tracks=tracks)


@app.route('/remove_track/<int:id_playlist>/<int:id_track>')
def remove_track(id_playlist, id_track):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    owner = execute_query("SELECT idu FROM playlist WHERE idp=%s", (id_playlist,), fetch_one=True)
    if owner and owner[0] == session['user_id']:
        execute_query("DELETE FROM possede WHERE idp=%s AND idm=%s", (id_playlist, id_track))
        flash("Morceau retiré.", "success")
    
    return redirect(url_for('edit_playlist', id_playlist=id_playlist))

@app.route('/delete_playlist/<int:id_playlist>')
def delete_playlist(id_playlist):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    execute_query("DELETE FROM playlist WHERE idp=%s AND idu=%s", (id_playlist, session['user_id']))
    flash("Playlist supprimée.", "success")
    return redirect(url_for('profile'))

@app.route('/toggle_follow/<int:id_groupe>')
def toggle_follow(id_groupe):
    if 'user_id' not in session: return redirect(url_for('login'))
    
    uid = session['user_id']
    
    exists = execute_query("SELECT * FROM suit WHERE idu=%s AND idg=%s", (uid, id_groupe), fetch_one=True)
    
    if exists:
        
        execute_query("DELETE FROM suit WHERE idu=%s AND idg=%s", (uid, id_groupe))
    else:
        execute_query("INSERT INTO suit (idu, idg) VALUES (%s, %s)", (uid, id_groupe))
        
    return redirect(url_for('group_page', id_groupe=id_groupe))


@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    user_id = session['user_id']

    if request.method == 'POST':
        new_pseudo = request.form['pseudo']
        new_email = request.form['email']

        try:
            execute_query(
                "UPDATE utilisateur SET pseudo = %s, email = %s WHERE idu = %s",
                (new_pseudo, new_email, user_id)
            )
            
            session['pseudo'] = new_pseudo
            
            flash("Profil mis à jour avec succès !", "success")
            return redirect(url_for('profile')) 
            
        except Exception as e:
            flash(f"Erreur lors de la mise à jour : {e}", "error")
            return redirect(url_for('edit_profile'))

    current_info = execute_query(
        "SELECT idu, pseudo, email FROM utilisateur WHERE idu = %s", 
        (user_id,), 
        fetch_one=True
    )

    return render_template('edit_profile.html', user=current_info)


if __name__ == '__main__':
    app.run(debug=True)