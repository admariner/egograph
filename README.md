# egograph

## About
* Network graph from google autocomplete suggestions. 
* Inspired by https://medium.com/applied-data-science/the-google-vs-trick-618c8fd5359f.

## Development
The website uses Flask (a python framework) and is hosted on Heroku. It can be run locally for development.

1. Clone the development GitHub repo (called "src") into the folder of your choice.
    ```bash
    git clone https://github.com/ekerstein/egograph.git src
    ```
2. Install and setup virtual environment.
    ```bash
    pip install virtualenv
    virtualenv env
    ```
3. Activate environment 
    * Mac
    ```bash
    source /path/to/env/bin/activate
    ```
    * Windows
    ```bash
    /path/to/env/Scripts/activate
    ```
4. Change directories into the src folder.
    ```bash
    cd src
    ```
5. Install python dependencies
    ```bash
    pip install -r requirements.txt
    ``` 
6. Start Flask local development server.
    * Set `app.debug = True` in deploy.py. Remember to set back to False before putting into production. 
    * The server can be reached at http://localhost:5000. 
    ```bash
    python deploy.py
    ```