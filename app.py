import os                                                                       # Operating system functions
import subprocess                                                               # Subprocess management
from flask import Flask, render_template, request, redirect, url_for, jsonify   # Flask framework
from werkzeug.utils import secure_filename                                      # Secure file uploads
import zipfile                                                                  # Zip file handling
import logging                                                                  # Logging functionality


app = Flask(__name__)

# Configure the built-in Python logging module
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] [%(levelname)s   ] %(name)s: %(message)s', datefmt="%Y-%m-%d %H:%M:%S")

# Dictionary to store project processes
project_processes = {}


@app.route('/')
def index():

    return render_template('index.html')


@app.route('/projects', methods=['GET', 'POST'])
def projects():
    display_projects = os.listdir('projects')
    running_projects, done_projects, crashed_projects = get_project_status(project_processes)

    return render_template(template_name_or_list='projects.html',
                           display_projects=display_projects,
                           running_projects=running_projects,
                           crashed_projects=crashed_projects,
                           done_projects=done_projects)


@app.route('/project/<project_name>')
def view_project(project_name):
    running_projects, done_projects, crashed_projects = get_project_status(project_processes)

    return render_template(template_name_or_list='view_project.html',
                           project_name=project_name,
                           running_projects=running_projects,
                           crashed_projects=crashed_projects,
                           done_projects=done_projects
                           )


@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        if 'file' not in request.files:
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)
        if file and file.filename.endswith('.zip'):
            filename = secure_filename(file.filename)
            zip_filepath = os.path.join('projects', filename)
            project_filepath = os.path.join('projects')
            file.save(zip_filepath)

            # Extract the zip file
            with zipfile.ZipFile(zip_filepath, 'r') as zip_ref:
                zip_ref.extractall(project_filepath)
                zip_ref.close()
            os.remove(zip_filepath)

            return redirect(url_for('index'))
    return render_template('upload.html')


@app.route('/start_project/<project_name>', methods=['GET'])
def start_project(project_name):
    projects_directory = os.path.join('projects')
    project_directory = os.path.join(projects_directory, project_name)

    # Create virtual environment and install dependencies
    create_virtualenv(project_directory)

    # Activate the virtual environment and execute main.py
    activate_cmd = os.path.join(project_directory, '.venv', 'Scripts', 'activate')
    main_py_path = os.path.join(project_directory, 'main.py')

    # Start the project in a separate subprocess and store the subprocess object
    project_process = subprocess.Popen([activate_cmd, '&&', 'python', main_py_path], shell=True)

    # Store the project process in the dictionary
    project_processes[project_name] = project_process

    return redirect(url_for('view_project', project_name=project_name))


@app.route('/stop_project/<project_name>', methods=['GET'])
def stop_project(project_name):
    # Check if the project is currently running
    if project_name in project_processes:
        # Check if the project process has terminated
        if project_processes[project_name].poll() is None:
            # If the process is still running, kill it
            subprocess.Popen(['taskkill', '/F', '/T', '/PID', str(project_processes[project_name].pid)])

            # Deactivate the virtual environment
            deactivate_cmd = 'deactivate'
            subprocess.Popen([deactivate_cmd], cwd=os.path.join('projects', project_name), shell=True)

        # Remove the project process from the dictionary
        del project_processes[project_name]

    return redirect(url_for('view_project', project_name=project_name))



@app.route('/project/<project_name>/log')
def get_project_log(project_name):
    log_directory = os.path.join('projects', project_name, 'logs')
    log_content = ""
    if os.path.exists(log_directory):
        log_files = [f for f in os.listdir(log_directory) if f.endswith('.log')]
        if log_files:
            latest_log_file = max(log_files)
            with open(os.path.join(log_directory, latest_log_file), 'r') as f:
                log_content = f.read()

    return jsonify(log_content=log_content)


def create_virtualenv(project_directory):
    """
    Create a virtual environment if it doesn't exist and install required dependencies.
    """
    venv_path = os.path.join(project_directory, '.venv')
    if not os.path.exists(venv_path):
        subprocess.run(['python', '-m', 'venv', venv_path], check=True)

        # Install required packages from requirements.txt
        requirements_file = os.path.join(project_directory, 'requirements.txt')
        if os.path.exists(requirements_file):
            subprocess.run([os.path.join(venv_path, 'Scripts', 'pip'), 'install', '-r', requirements_file], check=True)


def get_project_status(processes):
    running_projects = []
    done_projects = []
    crashed_projects = []

    for project_name, process in processes.items():
        if process.poll() is None:
            running_projects.append(project_name)
        elif process.poll() == 0:
            done_projects.append(project_name)
        else:
            crashed_projects.append(project_name)

    return running_projects, done_projects, crashed_projects


if __name__ == '__main__':
    app.run()
