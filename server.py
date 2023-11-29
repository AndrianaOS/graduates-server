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
@app.route("/allGraduates")
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

        return jsonify({"All Graduates": all_results}), 200

    except Exception as error:
        print("Error message:", str(error))
        traceback.print_exc()
        return jsonify({"Error message": str(error)}), 500


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
@app.route("/graduate", methods=["POST"])
def graduate():
    try:
        GITHUB_HEADERS = {
            "Authorization": f"Bearer {gh_token}",
            "Content-Type": "application/json",
        }

        with db_conn.cursor() as cursor:
            cursor.execute(GET_ALL_GITHUB_LINKS)
            all_github_data = cursor.fetchall()
            print(all_github_data)

            # github_usernames = [extract_github_username(
            #     url[0]) for url in all_github_links]
            # print(f"GitHub usernames:", github_usernames)
            for user_data in all_github_data:
                github_url = user_data[1]
                user_id = user_data[0]
                username = extract_github_username(github_url)
                print(username)

            all_usernames = {}

            # for username in github_usernames:
            #     print(username)
            #     if username is not None:
            #         github_query_json = {
            #             "query": f'{{user(login: "{username}"){{avatarUrl(size: 256), bio, email, websiteUrl, socialAccounts(first: 1){{nodes {{url}}}} }} }}'}

            #         response = request.post(os.getenv(
            #             "GITHUB_API_ENDPOINT"), json=github_query_json, headers=GITHUB_HEADERS)
            #         result = response.json()
            #         all_usernames[username] = result
            #     else:
            #         return jsonify({"Error": "Failed to retrieve data"})

            #     return jsonify(all_usernames)

            if username is not None:
                github_query_json = {
                    "query": f'{{user(login: "{username}"){{avatarUrl(size: 256), bio, email, websiteUrl, socialAccounts(first: 1){{nodes {{url}}}} }} }}'}

                response = requests.post(os.getenv(
                    "GITHUB_API_ENDPOINT"), json=github_query_json, headers=GITHUB_HEADERS)
                result = response.json()
                result["id"] = user_id
                all_usernames[username] = result
            else:
                return jsonify({"Error": "Failed to retrieve data"})

            return jsonify(all_usernames)
    except Exception as error:
        print("Error:", str(error))
        return jsonify({"Error": str(error)}), 500

# from flask import jsonify
# import os
# import psycopg2
# from dotenv import load_dotenv
# from flask import Flask, request, jsonify, make_response
# from flask_cors import CORS
# # import requests
# import traceback

# load_dotenv()

# app = Flask(__name__)
# CORS(app)


# # Connection to database
# db_url = os.getenv("DB_URL")
# db_conn = psycopg2.connect(db_url)

# INSERT_GRADUATE_RETURN_ID = "INSERT INTO graduates_data (name, github_url, role, cv_link) VALUES (%s, %s, %s, %s) RETURNING id"
# GET_GRADUATE_NAME = "SELECT 1 FROM graduates_data WHERE name = (%s)"
# GET_ALL_GRADUATES = "SELECT * FROM graduates_data"
# GET_GRADUATE_ID = "SELECT id, name FROM graduates_data WHERE name = (%s)"
# GET_ALL_GITHUB_LINKS = "SELECT github_url FROM graduates_data"


# # Route that hits the root of the server. Use this to make sure the server is running
# @app.route("/")
# def create_server():
#     return "Hello server. I am running"


# # Preliminary information used to run code to make sure it works
# trainee_data = {
#     "id": 0,
#     "trainee_name": "Andriana",
#     "github_link": "https://github.com/AndrianaOS",
#     "portfolio_link": "https://cv-portfolio.onrender.com/",
#     "linkedIn_link": "https://www.linkedin.com/in/andriana-saffo/",
#     "role": "Full Stack",
#     "about_me": "Lorem",
#     "skills": ["HTML", "Python", "JavaScript", "NodeJS", "CSS", "Flask", "PostgreSQL", "ExpressJS", "React"],
# }

# # Submitting form will add graduate data to this array. The data will not persist
# all_data = [trainee_data]

# # GitHub token
# gh_token = os.getenv("GITHUB_API_TOKEN")

# # Gets list of all graduates added to the array. To be refactored once database is established


# @app.route("/graduatesList", methods=["GET"])
# def graduates_list():
#     try:
#         with db_conn.cursor() as cursor:
#             cursor.execute(GET_ALL_GRADUATES)
#             result = cursor.fetchall()

#             if not result:
#                 response = make_response(jsonify(
#                     {"error": "List is empty"}), 400)
#             else:
#                 column_names = [desc[0] for desc in cursor.description]
#                 all_results = [dict(zip(column_names, row)) for row in result]
#                 response = make_response(
#                     jsonify({"all graduates": all_results}))

#             return response
#     except Exception as error:
#         print(error)
#         # return error
#         return jsonify({"error": str(error)}), 500


# # Extracts GitHub username from github_link
# def extract_alphanumeric_details(url):
#     prefix = "https://github.com/"

#     # Check if the URL starts with the specified prefix
#     if url.startswith(prefix):
#         # Extract the substring after the prefix
#         details = url[len(prefix):]

#         # Filter out non-alphanumeric characters
#         alphanumeric_details = ''.join(
#             char for char in details if char.isalnum())

#         return alphanumeric_details

#     else:
#         # Return None if the prefix is not present
#         return None


# # Example usage:
# # extracted_result = extract_alphanumeric_details(trainee_data["github_link"])
# # print("Extracted result:", extracted_result)


# # Interacts with GitHub API to pull information stated in query. User login will take users GitHub username
# @app.route("/graduates", methods=["POST"])
# def graduates():
#     try:
#         GITHUB_HEADERS = {
#             "Authorization": f"Bearer {gh_token}",
#             "Content-Type": "application/json",
#         }

#         with db_conn.cursor() as cursor:
#             cursor.execute(GET_ALL_GITHUB_LINKS)
#             github_links = cursor.fetchall()

#         github_names = [extract_alphanumeric_details(
#             link[0]) for link in github_links]
#         print("Github Names:", github_names)

#         all_results = {}
#         # all_results = []

#         for github_name in github_names:
#             print(github_name)
#             if github_name is not None:
#                 # github_query_json = {
#                 #     "query": f'{{user(login: "{github_names}"){{avatarUrl(size: 256), name, bio, email, websiteUrl, repositoriesContributedTo(first: 10){{totalCount}}, pinnedItems(first: 10) {{nodes {{... on Repository {{name}}}}}}}}}}'
#                 # }
#                 github_query_json = {
#                     "query": f'{{user(login: "{github_name}"){{avatarUrl(size: 256), name, email, websiteUrl}}}}'
#                 }
#                 response = requests.post(
#                     os.getenv("GITHUB_API_ENDPOINT"), json=github_query_json, headers=GITHUB_HEADERS)
#                 result = response.json()
#                 print(result)
#                 all_results[github_name] = result
#                 # all_results.append(result)

#             else:
#                 return jsonify({"error": "Failed to extract login details"}), 400
#         print(all_results)
#         return jsonify(all_results)
#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


# # with db_conn.cursor() as cursor:
# #     cursor.execute(GET_ALL_GITHUB_LINKS)
# #     github_links = cursor.fetchall()

# # # Extract GitHub names using the extract function
# # github_names = [extract_alphanumeric_details(link[0]) for link in github_links]

# # # Print the extracted GitHub names
# # print("GitHub Names:", github_names)


# # POST request for form
# @app.route("/submit_trainee_form", methods=["GET", "POST", "OPTIONS"])
# def submit_trainee_form():
#     try:
#         print("Request method:", request.method)
#         print("What happens here:", request.get_json())

#         data = request.get_json()
#         print("This comes through:", data)
#         trainee_name = data["trainee_name"]
#         print("Name that comes through", trainee_name)
#         github_link = data["github_link"]
#         portfolio_link = data["portfolio_link"]
#         linkedIn_link = data["linkedIn_link"]
#         role = data["role"]
#         about_me = data["about_me"]
#         skills = data["skills"]

#         with db_conn:
#             with db_conn.cursor() as cursor:
#                 cursor.execute(GET_GRADUATE_NAME, (trainee_name,))
#                 existing_graduate_name = cursor.fetchone()

#             if existing_graduate_name:
#                 raise ValueError(f"Graduate {trainee_name} already exists")

#         #     required_fields = ["trainee_name", "github_link",
#         #                        "portfolio_link", "linkedIn_link", "role", "about_me", "skills"]

#         #     if any(not data[field] for field in required_fields):
#         #         raise ValueError("Please fill in required fields")

#         #     cursor.execute(INSERT_GRADUATE_RETURN_ID, (trainee_name, github_link,
#         #                    portfolio_link, linkedIn_link, role, about_me, skills,))

#         #     cursor.execute(GET_GRADUATE_ID, (trainee_name,))
#         #     graduate_id = cursor.fetchone()[0]
#         #     print("Graduate ID for trainee", graduate_id)
#         # db_conn.commit()
#         # return jsonify({"id": graduate_id, "message": f"{trainee_name} successfully added"}), 201
#         with db_conn:
#             with db_conn.cursor() as cursor:
#                 required_fields = ["trainee_name", "github_link",
#                                    "portfolio_link", "linkedIn_link", "role", "about_me", "skills"]

#                 if any(not data[field] for field in required_fields):
#                     raise ValueError("Please fill in required fields")

#                 cursor.execute(INSERT_GRADUATE_RETURN_ID, (trainee_name, github_link,
#                                                            portfolio_link, linkedIn_link, role, about_me, skills))

#                 cursor.execute(GET_GRADUATE_ID, (trainee_name,))
#                 graduate_id = cursor.fetchone()[0]

#         db_conn.commit()
#         return jsonify({"id": graduate_id, "message": f"{trainee_name} successfully added"}), 201
#     except Exception as error:
#         # Convert the exception to a string
#         print("This is the error message:", str(error))
#         traceback.print_exc()  # Print the traceback for more details
#         return jsonify({"error": str(error)}), 500
