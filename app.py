import logging
import math
from datetime import datetime
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask import render_template
from flask import request
from flask import redirect

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///vault.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

logging.basicConfig(
    filename='logs/app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logging.info("Application Started")


db = SQLAlchemy(app)
class Note(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    title = db.Column(
        db.String(100),
        nullable=False
    )

    content = db.Column(
        db.Text,
        nullable=False
    )

    tag = db.Column(
        db.String(50)
    )

    link = db.Column(
        db.String(300)
    )

    source = db.Column(
    db.String(50)
    )

    important = db.Column(
    db.Boolean,
    default=False
   )


def estimate_reading_time(text):
    words = len(text.split())
    minutes = max(1, math.ceil(words / 200))
    return f"{minutes} min read"


@app.template_filter('reading_time')
def reading_time_filter(content):
    return estimate_reading_time(content or "")


def get_dashboard_counts():
    return {
        'total_notes': Note.query.count(),
        'important_notes': Note.query.filter_by(important=True).count(),
        'whatsapp_notes': Note.query.filter_by(source='WhatsApp').count(),
        'telegram_notes': Note.query.filter_by(source='Telegram').count(),
        'youtube_notes': Note.query.filter_by(source='YouTube').count(),
        'instagram_notes': Note.query.filter_by(source='Instagram').count(),
    }


@app.route('/')
def home():

    notes = Note.query.all()
    counts = get_dashboard_counts()

    return render_template(
        "index.html",
        notes=notes,
        current_year=datetime.now().year,
        **counts
    )

@app.route('/add', methods=['GET', 'POST'])
def add_note():

    if request.method == 'POST':

        title = request.form['title']
        content = request.form['content']
        tag = request.form['tag']
        link = request.form['link']
        source = request.form['source']
        important = request.form['important']
        is_important = (important == "Yes")

        note = Note(
            title=title,
            content=content,
            tag=tag,
            link=link,
            source=source,
            important=is_important
)

        db.session.add(note)
        db.session.commit()

        logging.info(f"Note Added: {title}")

        return redirect('/')

    return render_template("add_note.html")

@app.route('/search')
def search():

    keyword = request.args.get('q', '')

    if keyword:
        notes = Note.query.filter(
            Note.title.contains(keyword)
        ).all()
    else:
        notes = Note.query.all()

    counts = get_dashboard_counts()

    return render_template(
        'index.html',
        notes=notes,
        current_year=datetime.now().year,
        **counts
    )

@app.route('/delete/<int:id>')
def delete_note(id):

    note = Note.query.get(id)

    logging.warning(
        f"Deleted {note.title}"
    )

    db.session.delete(note)

    db.session.commit()

    return redirect('/')

@app.route('/edit/<int:id>', methods=['GET', 'POST'])
def edit_note(id):

    note = Note.query.get_or_404(id)

    if request.method == 'POST':

        note.title = request.form['title']
        note.content = request.form['content']
        note.tag = request.form['tag']
        note.link = request.form['link']

        db.session.commit()

        logging.info(f"Note Updated: {note.title}")

        return redirect('/')

    return render_template(
        'edit_note.html',
        note=note
    )

@app.route('/note/<int:id>')
def read_note(id):

    note = Note.query.get_or_404(id)
    reading_time = estimate_reading_time(note.content)

    return render_template(
        'read_note.html',
        note=note,
        reading_time=reading_time,
        current_year=datetime.now().year,
        **get_dashboard_counts()
    )

if __name__ == "__main__":

    with app.app_context():
        db.create_all()
    app.run(debug=True)