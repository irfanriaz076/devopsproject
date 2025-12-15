from flask import Flask, render_template, request, redirect, url_for
import pymysql
import os
from prometheus_flask_exporter import PrometheusMetrics  # new

app = Flask(__name__)
metrics = PrometheusMetrics(app)  # new: exposes /metrics on port 5000

# Database configuration
db_config = {
    'host': os.getenv('DB_HOST', 'mysql-service'),
    'user': os.getenv('DB_USER', 'root'),
    'password': os.getenv('DB_PASSWORD', 'password'),
    'database': os.getenv('DB_NAME', 'taskdb'),
    'port': int(os.getenv('DB_PORT', 3306))
}

def get_db_connection():
    return pymysql.connect(**db_config)

@app.route('/')
def index():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks")
        tasks = cursor.fetchall()
        cursor.close()
        conn.close()
        return render_template('index.html', tasks=tasks)
    except Exception as e:
        return f"Database Error: {str(e)}"

@app.route('/add', methods=['POST'])
def add_task():
    task = request.form['task']
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO tasks (task_name) VALUES (%s)", (task,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for('index'))

@app.route('/health')
def health():
    return {'status': 'healthy'}, 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
