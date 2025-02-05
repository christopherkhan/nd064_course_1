import sqlite3
from flask import Flask, jsonify, json, render_template, request, url_for, redirect, flash
from werkzeug.exceptions import abort
import logging
import sys


# Function to get a database connection.
# This function connects to database with the name `database.db`
def get_db_connection():
    global db_connections_count
    connection = sqlite3.connect('database.db')
    connection.row_factory = sqlite3.Row
    db_connections_count += 1
    return connection


# Function to get a post using its ID
def get_post(post_id):
    connection = get_db_connection()
    post = connection.execute('SELECT * FROM posts WHERE id = ?',
                        (post_id,)).fetchone()
    connection.close()
    return post


# Define the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'
db_connections_count = 0


# Define the main route of the web application 
@app.route('/')
def index():
    connection = get_db_connection()
    posts = connection.execute('SELECT * FROM posts').fetchall()
    connection.close()
    return render_template('index.html', posts=posts)


# Health check
@app.route('/healthz')
def healthz():
    response = app.response_class(
        response=json.dumps({"result": "OK - healthy"}),
        status=200,
        mimetype='application/json'
    )
    return response


# Metrics
@app.route('/metrics')
def metrics():
    # get post count
    connection = get_db_connection()
    post_count = connection.execute('SELECT COUNT(*) FROM posts').fetchone()
    connection.close()

    response = app.response_class(
        response=json.dumps({"db_connection_count": db_connections_count, "post_count":post_count[0]}),
        status=200,
        mimetype='application/json'
    )
    return response


# Define how each individual article is rendered 
# If the post ID is not found a 404 page is shown
@app.route('/<int:post_id>')
def post(post_id):
    post = get_post(post_id)
    if post is None:
        app.logger.error("Non existing article was accessed. 404 Page returned")
        return render_template('404.html'), 404
    else:
        app.logger.info("Article, '{}' retrieved!".format(post['title']))
        return render_template('post.html', post=post)


# Define the About Us page
@app.route('/about')
def about():
    app.logger.info('The About Us page was retrieved')
    return render_template('about.html')


# Define the post creation functionality 
@app.route('/create', methods=('GET', 'POST'))
def create():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']

        if not title:
            flash('Title is required!')
        else:
            connection = get_db_connection()
            connection.execute('INSERT INTO posts (title, content) VALUES (?, ?)',
                         (title, content))
            connection.commit()
            connection.close()
            app.logger.info("New article '{}' created!".format(title))
            return redirect(url_for('index'))

    return render_template('create.html')


# start the application on port 3111
if __name__ == "__main__":
    logger = logging.getLogger()
    logger.handlers = []
    #logger.handlers.clear()
    logger.setLevel(logging.DEBUG)

    log_format = '%(levelname)s:%(name)s: %(asctime)s, %(message)s'
    date_format = '%d/%b/%Y, %H:%M:%S'

    sysout_handler = logging.StreamHandler(sys.stdout)
    sysout_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(fmt=log_format, datefmt=date_format)
    sysout_handler.setFormatter(formatter)
    logger.addHandler(sysout_handler)

    syserr_handler = logging.StreamHandler(sys.stderr)
    syserr_handler.setLevel(logging.WARNING)
    syserr_handler.setFormatter(formatter)
    logger.addHandler(syserr_handler)
    app.run(host='0.0.0.0', port='3111')
