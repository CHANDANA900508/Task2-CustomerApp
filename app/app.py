from flask import Flask, jsonify, request
import os
import mysql.connector

app = Flask(__name__)

ENVIRONMENT = os.getenv("ENVIRONMENT", "DEV")
VERSION = os.getenv("VERSION", "1.0")

DB_HOST = os.getenv("DB_HOST", "customer-db-dev")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "root123")
DB_NAME = os.getenv("DB_NAME", "customerdb")


@app.route("/")
def home():
    return jsonify({
        "application": "Customer Application",
        "environment": ENVIRONMENT,
        "version": VERSION,
        "message": "Customer application is running"
    })


@app.route("/health")
def health():
    return jsonify({
        "status": "UP",
        "environment": ENVIRONMENT,
        "version": VERSION
    })


@app.route("/db-health")
def db_health():
    try:
        connection = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME
        )

        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        result = cursor.fetchone()

        cursor.close()
        connection.close()

        return jsonify({
            "database": "UP",
            "db_host": DB_HOST,
            "result": result[0]
        })

    except Exception as e:
        return jsonify({
            "database": "DOWN",
            "error": str(e)
        }), 500


@app.route("/customers/search")
def search_customer():
    name = request.args.get("name", "")

    return jsonify({
        "feature": "customer-search",
        "search_name": name,
        "message": f"Searching customers for: {name}"
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)