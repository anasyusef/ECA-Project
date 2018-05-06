# ECA-Project
**Before running the website, make sure you have flask installed.**

In order to run the app, the following steps need to be done:
1. Clone the repository
2. Inside the ECA-Project-master folder activate the virtual environment with the `source venv/bin/activate` command:

3. Run the `export FLASK_APP=ecaproject.py` command

Before running the app the database settings needs to be amended from the `config.py` file.

4. Run the `pip install -r requirements.txt` command in order to install the required Python packages for the website

In order to create the tables into the database and add some data open the shell within the app context with the `flask shell` command

In the shell run the `setup_db()` function

Then, quit from the shell and run the app with flask (`flask run`), and you should have the website running.
