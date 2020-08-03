import sqlite3 as sql

from flask import Flask, render_template

app = Flask(__name__)

@app.route('/home')
@app.route('/')
def home():
    return render_template('home.html')

@app.route('/teams')
def teams():
    con = sql.connect('data.db')
    con.row_factory = sql.Row

    cur = con.cursor()
    cur.execute('SELECT * FROM teams')

    rows = cur.fetchall()
    return render_template('teams.html', rows=rows)

@app.route('/players')
def players():
    con = sql.connect('data.db')
    con.row_factory = sql.Row

    cur = con.cursor()
    cur.execute('SELECT * FROM players')

    rows = cur.fetchall()
    return render_template('players.html', rows=rows)
    
app.run(host='0.0.0.0', debug=True)