# egograph

## About
Network graph of Google search suggestions.

## Development
The website uses Django (a python framework) and is hosted on Heroku. It can be run locally for development.

1. Clone the development GitHub repo (called "src") into the folder of your choice.
    ```bash
    git clone https://github.com/ekerstein/egograph.git src
    ```
2. Install and setup virtual environment.
    ```bash
    pip install virtualenv
    virtualenv env
    ```
3. Activate environment.
    * Mac
    ```bash
    source /path/to/env/bin/activate
    ```
    * Windows
    ```bash
    /path/to/env/scripts/activate
    ```
4. Change directories into the src folder.
    ```bash
    cd src
    ```
5. Install python dependencies.
    ```bash
    pip install -r requirements.txt
    ``` 
6. Setup local database. 
    * Install [PostgreSQL](https://www.postgresql.org/).
    * Setup username and password. Update these in the `config/conf/dev/settings.py` file.
    * Create a database called "egograph" upon setup or in pgAdmin.
7. Make initial database migrations.
    ```bash
    python manage.py migrate
    ```
8. Make superuser.
    ```bash
    python manage.py createsuperuser
    ```
9. Start Django local server.
    The server can be reached at http://localhost:8000.
    ```bash
    python manage.py runserver
    ```