import ast
import atexit
from curses import flash
from flask import Flask, request, render_template, redirect, url_for, flash
from werkzeug.utils import secure_filename
from flask import session
import os

app = Flask(__name__, static_folder="public")
# app.secret_key = "TODO_task3"

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
    return render_template("index.html", wallpapers=wallpapers, session=session)

@app.route("/login", methods=["GET", "POST"])
def login():
    error_msg = ""

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
    return render_template("login.html", session=session, error_msg=error_msg)

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

        save_path = os.path.join(app.config['public/wallpapers'], theme, name)
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


@app.route('/delete_image', methods=['POST'])
def delete_image():
    theme = request.form['theme']
    image_path = request.form['image_path']
    
    full_image_path = os.path.join('public', 'wallpapers', theme, image_path)
    
    try:
        if os.path.exists(full_image_path):
            os.remove(full_image_path)
            wallpapers[theme].remove(image_path)

            if not wallpapers[theme]:
                wallpapers.pop(theme)
                os.rmdir(os.path.join('public', 'wallpapers', theme))

            write_database(DATABASE_FILE)
            read_database(DATABASE_FILE)
        else:
            print("The file does not exist")
    except Exception as e:
        print(f"Error deleting image: {e}")

    return redirect(url_for('index'))

@app.route('/delete_all_images', methods=['POST'])
def delete_all_images():
    theme = request.form['theme']
    
    theme_dir = os.path.join('public', 'wallpapers', theme)
    
    try:
        for image_path in wallpapers.get(theme, []):
            full_image_path = os.path.join(theme_dir, image_path)
            if os.path.exists(full_image_path):
                os.remove(full_image_path)
        
        wallpapers[theme] = []

        wallpapers.pop(theme)
        os.rmdir(theme_dir)

        write_database(DATABASE_FILE)
        read_database(DATABASE_FILE)
        
    except Exception as e:
        print(f"Error deleting images: {e}")

    return redirect(url_for('index'))

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


@app.errorhandler(404)
def error404(code):
    return "HTTP Error 404 - Page Not Found"

if __name__ == "__main__":
    app.run(debug=True, port=5000)

