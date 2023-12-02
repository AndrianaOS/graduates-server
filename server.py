from flask import Flask, jsonify, request
import traceback
from flask_cors import CORS
from dotenv import load_dotenv
import os
import psycopg2
import requests

load_dotenv()

app = Flask(__name__)
CORS(app)

db_url = os.getenv("DB_URL")
db_conn = psycopg2.connect(db_url)
gh_token = os.getenv("GITHUB_API_TOKEN")

INSERT_GRADUATE_RETURN_ID = "INSERT INTO graduates_data (name, github_url, role, cv_link) VALUES (%s, %s, %s, %s) RETURNING id"
GET_GRADUATE_NAME = "SELECT 1 FROM graduates_data WHERE name = (%s)"
GET_ALL_GRADUATES = "SELECT * FROM graduates_data"
GET_GRADUATE_ID = "SELECT id, name FROM graduates_data WHERE name = (%s)"
GET_ALL_GITHUB_LINKS = "SELECT id, github_url FROM graduates_data"


# ROUTE TO MAKE SURE SERVER IS RUNNING AND CONNECTED
@app.route("/")
def get_home():
    traceback.print_exc()
    return "Hello Server. Im running now"


# ROUTE TO GET ALL GRADUATES IN DATABASE
# @app.route("/allGraduates")
# def all_graduates():
#     try:
#         with db_conn.cursor() as cursor:
#             cursor.execute(GET_ALL_GRADUATES)
#             cursor_result = cursor.fetchall()

#             if not cursor_result:
#                 response = jsonify({"error": "No graduates available"}), 400
#                 return response

#             column_names = [each_description[0]
#                             for each_description in cursor.description]
#             all_results = [dict(zip(column_names, row))
#                            for row in cursor_result]

#         return jsonify(all_results), 200

#     except Exception as error:
#         print("Error message:", str(error))
#         traceback.print_exc()
#         return jsonify({"Error message": str(error)}), 500


# ROUTE TO POST GRADUATE INFORMATION INTO DATABASE
@app.route("/submit_graduate", methods=["GET", "POST"])
def submit_graduate():
    try:
        grad_data = request.get_json()
        name = grad_data["name"]
        github_url = grad_data["github_url"]
        role = grad_data["role"]
        cv_link = grad_data["cv_link"]
        with db_conn:
            with db_conn.cursor() as cursor:
                cursor.execute(GET_GRADUATE_NAME, (name,))
                existing_graduate_name = cursor.fetchone()

                if existing_graduate_name:
                    raise ValueError(f"Graduate {name} already exists")

                required_fields = ["name", "github_url", "role", "cv_link"]

                if any(not grad_data[field] for field in required_fields):
                    raise ValueError("Please fill in all required fields")

                cursor.execute(INSERT_GRADUATE_RETURN_ID,
                               (name, github_url, role, cv_link))

                cursor.execute(GET_GRADUATE_ID, (name,))
                graduate_id = cursor.fetchone()[0]

            db_conn.commit()
            return jsonify({"id": graduate_id, "message": f"{name} successfully added"}), 201

    except Exception as error:
        print("Error message:", str(error))
        traceback.print_exc()  # Print the traceback for more details
        return jsonify({"error": str(error)}), 500


# FUNCTION TO EXTRACT GITHUB USERNAME FROM GITHUB_LINK IN DATABASE
def extract_github_username(url):
    prefix = "https://github.com/"

    if url.startswith(prefix):
        details = url[len(prefix):]

        username = "".join(char for char in details if char.isalnum())

        return username


# ROUTE TO INTERACT WITH GITHUB GRAPHQL API TO PULL INFORMATION
# @app.route("/graduate", methods=["POST"])
# def graduate():
#     try:
#         GITHUB_HEADERS = {
#             "Authorization": f"Bearer {gh_token}",
#             "Content-Type": "application/json",
#         }

#         with db_conn.cursor() as cursor:
#             cursor.execute(GET_ALL_GITHUB_LINKS)
#             all_github_data = cursor.fetchall()
#             print(all_github_data)

#             # github_usernames = [extract_github_username(
#             #     url[0]) for url in all_github_links]
#             # print(f"GitHub usernames:", github_usernames)
#             for user_data in all_github_data:
#                 github_url = user_data[1]
#                 user_id = user_data[0]
#                 username = extract_github_username(github_url)
#                 print(username)

#             all_usernames = {}

#             # for username in github_usernames:
#             #     print(username)
#             #     if username is not None:
#             #         github_query_json = {
#             #             "query": f'{{user(login: "{username}"){{avatarUrl(size: 256), bio, email, websiteUrl, socialAccounts(first: 1){{nodes {{url}}}} }} }}'}

#             #         response = request.post(os.getenv(
#             #             "GITHUB_API_ENDPOINT"), json=github_query_json, headers=GITHUB_HEADERS)
#             #         result = response.json()
#             #         all_usernames[username] = result
#             #     else:
#             #         return jsonify({"Error": "Failed to retrieve data"})

#             #     return jsonify(all_usernames)

#             if username is not None:
#                 github_query_json = {
#                     "query": f'{{user(login: "{username}"){{avatarUrl(size: 256), bio, email, websiteUrl, socialAccounts(first: 1){{nodes {{url}}}} }} }}'}

#                 response = requests.post(os.getenv(
#                     "GITHUB_API_ENDPOINT"), json=github_query_json, headers=GITHUB_HEADERS)
#                 result = response.json()
#                 result["id"] = user_id
#                 all_usernames[username] = result
#             else:
#                 return jsonify({"Error": "Failed to retrieve data"})

#             return jsonify(all_usernames)
#     except Exception as error:
#         print("Error:", str(error))
#         return jsonify({"Error": str(error)}), 500

@app.route("/allGraduates", methods=["GET", "POST"])
def all_graduates():
    try:
        with db_conn.cursor() as cursor:
            cursor.execute(GET_ALL_GRADUATES)
            cursor_result = cursor.fetchall()

            if not cursor_result:
                response = jsonify({"error": "No graduates available"}), 400
                return response

            column_names = [each_description[0]
                            for each_description in cursor.description]
            all_results = [dict(zip(column_names, row))
                           for row in cursor_result]

            GITHUB_HEADERS = {
                "Authorization": f"Bearer {gh_token}",
                "Content-Type": "application/json",
            }

            cursor.execute(GET_ALL_GITHUB_LINKS)
            all_github_data = cursor.fetchall()
            print(all_github_data)

            all_data = []

            for graduate_data in all_results:
                graduate_github_name = graduate_data.get("github_url")
                if graduate_github_name:
                    username = extract_github_username(graduate_github_name)

                    if username is not None:
                        github_query_json = {
                            "query": f'{{user(login: "{username}"){{avatarUrl(size: 256), bio, email, websiteUrl, socialAccounts(first: 1){{nodes {{url}}}} }} }}'
                        }

                        response = requests.post(
                            os.getenv("GITHUB_API_ENDPOINT"),
                            json=github_query_json,
                            headers=GITHUB_HEADERS,
                        )
                        result = response.json()
                        result["id"] = graduate_data.get("id")

                        # Combine data based on GitHub username
                        all_data.append(
                            {"db_data": graduate_data, "github_data": result})
                    else:
                        return jsonify({"Error": f"Failed to extract GitHub username from: {graduate_github_name}"}), 400
                else:
                    return jsonify({"Error": "Graduate name is missing"}), 400

            return jsonify(all_data), 200

    except Exception as error:
        print("Error:", str(error))
        return jsonify({"Error": str(error)}), 500
