# ECA-Project

In order to run the app, the following steps need to be done:
1. Clone the repository
2. Inside the ECA-Project-master folder activate the virtual environment with the following command:

```source venv/bin/activate```

3. Run the following commands:

```export FLASK_APP=ecaproject.py```

Before running the app the database settings needs to be amended from the `config.py` file.

In order to create the tables into the database and add some data open the shell within the app context with the `flask shell` command

In the shell run the `setup_db()` function

Then, quit from the shell and run the app with flask, and you should have the website running.
