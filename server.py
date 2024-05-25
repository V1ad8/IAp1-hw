import ast
import atexit
from curses import flash
from flask import Flask, request, render_template, redirect, url_for, flash
from werkzeug.utils import secure_filename
from flask import session
import os

# Note: static folder means all files from there will be automatically served over HTTP
app = Flask(__name__, static_folder="public")
app.secret_key = "TODO_task3"

# TODO Task 02: you can use a global variable for storing the auth session
# e.g., add the "authenticated" (boolean) and "username" (string) keys.
session = {"authenticated": False, "username": ""}

ALLOWED_USERS = {
    "admin": "admin",
    "user": "password",
}

wallpapers = {}

DATABASE_FILE = "public/database.txt"

@app.context_processor
def inject_user():
    return dict(user=session)

def is_authenticated():
    return session.get("authenticated", False)

@app.route("/")
def index():
    wallpapers = read_database(DATABASE_FILE)
    return render_template("index.html", wallpapers=wallpapers)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if ALLOWED_USERS.get(username) == password:
            session["authenticated"] = True
            session["username"] = username
            return redirect("/")
        else:
            error_msg = "Wrong username or password. Please try again."
            pass
    return render_template("login.html")

app.config['UPLOAD_FOLDER'] = 'public/wallpapers'

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if not session["authenticated"]:
        return redirect("/login")

    if request.method == 'POST':
        file = request.files['file']
        theme = request.form.get("theme", "")
        if theme == "custom":
            theme = request.form.get("custom_theme", "")
            os.system(f"mkdir -p public/uploads/\"{theme}\"")
        new_name = request.form.get("new_name", "")

        if new_name:
            name = new_name + "." + file.filename.split('.')[-1]
        else:
            name = file.filename

        save_path = os.path.join(app.config['UPLOAD_FOLDER'], theme, name)
        print(save_path)

        if os.path.exists(save_path):
            file.save(save_path)
            return redirect("/upload")
        
        if file and theme:
            file.save(save_path)

            current_files = wallpapers.get(theme, [])
            current_files.append(name)
            wallpapers[theme] = current_files

            write_database(DATABASE_FILE)
            read_database(DATABASE_FILE)

        
    predefined_themes = []
    for theme in wallpapers.keys():
        predefined_themes.append(theme)

    return render_template('upload.html', predefined_themes=predefined_themes, session=session)
    # return render_template('upload.html')

@app.route("/logout")
def logout():
    if not session["authenticated"]:
        return redirect("/")

    session["authenticated"] = False
    session["username"] = ""
    return redirect("/")

@app.context_processor
def inject_template_vars():
    return {
        "todo_var": "TODO_inject_common_template_variables"
    }


# You can use this as a starting point for Task 04
# (note: you need a "write" counterpart)
def read_database(filename):
    global wallpapers

    with open(filename, 'r') as file:
        for line in file:
            stripped_line = line.strip()
            if stripped_line:
                theme, files = stripped_line.split(": ", 1)
                theme = theme.strip('"')
                files = ast.literal_eval(files.rstrip(','))
                files.sort()
                wallpapers[theme] = files

    return dict(sorted(wallpapers.items()))

def write_database(filename):
    global wallpapers
    
    try:
        with open("public/tmp", "a") as file:
            file.seek(0)
            for theme, files in wallpapers.items():
                file.write(f'"{theme}": {files},\n')
    except Exception as e:
        print("Error:", e)

    file.close()

    file = open("public/tmp", "r")
    content = file.read()
    file.close()
    os.remove("public/tmp")

    file = open(filename, "w")
    file.write(content)
    file.close()

atexit.register(write_database, "public/out.txt")


@app.errorhandler(404)
def error404(code):
    # bonus: make it show a fancy HTTP 404 error page, with red background and bold message ;)
    return "HTTP Error 404 - Page Not Found"


# Run the web server (port 5000 - the default Flask port)
if __name__ == "__main__":
    app.run(debug=True, port=5000)

