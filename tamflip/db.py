import sqlite3
import click
from flask import current_app, g
from flask.cli import with_appcontext


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db

def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()

def init_db():
    db = get_db()
    with current_app.open_resource('schema.sql') as f:
        db.executescript(f.read().decode('utf8'))
        db.commit()

    val = db.execute('SELECT * FROM tracked_flights').fetchall()
    for i in val:
        print(tuple(i))


@click.command('init-db')
@with_appcontext
def init_db_command():
    """Clear DB and make new DB"""
    init_db()
    click.echo('Initialized Database')

@click.command('show-db')
@with_appcontext
def show_db_command():
    """Display db"""
    db = get_db()
    cursor = db.execute('SELECT * FROM tracked_flights')
    for row in cursor.fetchall():
        print(tuple(row))

# Function to link app with these commands
def init_app(app):
    app.teardown_appcontext(close_db)
    app.cli.add_command(init_db_command)
    app.cli.add_command(show_db_command)
