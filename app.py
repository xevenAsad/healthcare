import os
import pyodbc
from flask import Flask, request
from Bio import Entrez
import openai
import json
from flask_cors import CORS
from dotenv import load_dotenv


class Database:
    def __init__(self):
        # Load environment variables from .env file
        load_dotenv()

        # Get environment variables

        sql_host = os.environ.get('SQL_HOST')
        sql_UserId = os.environ.get('USERID')
        sql_passowrd = os.environ.get('PASSWORD')
        sql_database = os.environ.get('DATABASE')

        conn = pyodbc.connect('DRIVER={SQL Server};SERVER='+sql_host +
                              ';DATABASE='+sql_database+';UID='+sql_UserId+';PWD=' + sql_passowrd)

    def insert_user_details(self, email, username, phone, company, total_blogs, remaining_blogs, active_status, profile_pic, description, Password):
        sql = "INSERT INTO UserDetails (Email, UserName, Phone, Company, TotalBlogs, RemainingBlogs, ActiveStatus, ProfilePic, Description, Password) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)"
        cursor = self.conn.cursor()
        cursor.execute(sql, (email, username, phone, company, total_blogs,
                       remaining_blogs, active_status, profile_pic, description, Password))
        self.conn.commit()

    def insert_blog(self, title, description, created_by_id, request_id, is_active):
        sql = "INSERT INTO Blogs (Title, Description, CreatedById, RequestId, IsActive) VALUES (?, ?, ?, ?, ?)"
        cursor = self.conn.cursor()
        cursor.execute(
            sql, (title, description, created_by_id, request_id, is_active))
        self.conn.commit()

    def get_user_details(self, email):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM UserDetails WHERE Email = ?", (email,))
        row = cursor.fetchone()
        if row:
            user = {
                'Email': row[0],
                'UserName': row[1],
                'Phone': row[2],
                'Company': row[3],
                'TotalBlogs': row[4],
                'RemainingBlogs': row[5],
                'ActiveStatus': row[6],
                'ProfilePic': row[7],
                'Description': row[8],
                'Password': row[9]
            }
            return user
        else:
            return None


class OpenAIAPI:
    def __init__(self):
        openai.api_key = ' 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'

    def generate_blogpost(self, search_term):

        # preamble= f"Write an Article of approximately 500 words on '{search_term}' with in-text citations. Inclusion of in-text 'citations' of Latest Research is mandatory. Must Include a 'References' section at the end."
        prompt = f"Write an Article of approximately 500 words on '{search_term}' with in-text citations. Inclusion of in-text 'citations' of Latest Research is mandatory. Must Include a 'References' section at the end. Also give a catchy Title."
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant that writes blogposts on given topics."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2
            )
        except Exception as e:
            print(f'Error : {str(e)}')
        blogpost = response['choices'][0]['message']['content']
        if blogpost is not None:
            return blogpost
        else:
            return None


app = Flask(__name__)
CORS(app)

db = Database()
openai_api = OpenAIAPI()


@app.route('/users', methods=['POST'])
def save_user():
    payload = request.get_json()
    email = payload['Email']
    username = payload['UserName']
    phone = payload['Phone']
    company = payload['Company']
    total_blogs = payload['TotalBlogs']
    remaining_blogs = payload['RemainingBlogs']
    active_status = payload['ActiveStatus']
    profile_pic = payload['ProfilePic']
    description = payload['Description']
    Password = payload['Password']

    try:
        # Check if the email already exists in the database
        cursor = db.conn.cursor()
        cursor.execute(
            "SELECT Email FROM UserDetails WHERE Email = ?", (email,))
        existing_user = cursor.fetchone()
        if existing_user:
            return json.dumps({'status': 'error', 'message': 'User with this email already exists!'})

        # Insert the user details into the database
        db.insert_user_details(email, username, phone, company, total_blogs,
                               remaining_blogs, active_status, profile_pic, description, Password)

        return json.dumps({'status': 'success', 'User': payload})
    except Exception as e:
        print(str(e))
        return json.dumps({'status': 'error'})


@app.route('/blogs', methods=['POST'])
def save_blogpost():
    payload = request.get_json()
    title = payload['Title']
    created_by_id = payload['CreatedById']
    request_id = payload['RequestId']
    is_active = payload['IsActive']

    try:
        # Search PubMed for the given search term
        # description = entrez_api.search(title)
        # If description is not found, generate one using OpenAI GPT-3
        # if not description:
        #     print(description)
        print(title)
        description = openai_api.generate_blogpost(title)

        # Insert the blog post into the database
        db.insert_blog(title, description, created_by_id,
                       request_id, is_active)

        return json.dumps({'status': 'success', 'BlogPost': description})
    except Exception as e:
        print(str(e))
        return json.dumps({'status': 'error'})


@app.route('/GetAllUsers', methods=['GET'])
def get_users():
    try:
        cursor = db.conn.cursor()
        cursor.execute(
            "SELECT Email, UserName, Phone, Company, TotalBlogs, RemainingBlogs, ActiveStatus FROM UserDetails")
        rows = cursor.fetchall()
        users = []
        for row in rows:
            user = {
                'Email': row[0],
                'UserName': row[1],
                'Phone': row[2],
                'Company': row[3],
                'TotalBlogs': row[4],
                'RemainingBlogs': row[5],
                'ActiveStatus': row[6]
            }
            users.append(user)
        return json.dumps({'status': 'success', 'Users': users})
    except Exception as e:
        print(str(e))
        return json.dumps({'status': 'error'})


@app.route('/login', methods=['POST'])
def login():
    payload = request.get_json()
    email = payload['Email']
    password = payload['Password']
    try:
        cursor = db.conn.cursor()
        cursor.execute(
            "SELECT Email FROM UserDetails WHERE Email = ? AND Password = ?", (email, password))
        existing_user = cursor.fetchone()
        if existing_user:
            user = db.get_user_details(email)
            return json.dumps({'status': 'success', 'User': user})
        else:
            return json.dumps({'status': 'error', 'message': 'Invalid email or password'})
    except Exception as e:
        print(str(e))
        return json.dumps({'status': 'error'})


if __name__ == '__main__':
    db = Database()
    openai_api = OpenAIAPI()
    app.run(debug=True)
