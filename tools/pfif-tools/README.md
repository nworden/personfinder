# PFIF tools

## Development environment

First, if you don't already have it, install virtualenv:
`pip install virtualenv`

Then, from the `tools/pfif-tools` directory, run the following commands to set
up a virtual environment and install the dependencies:

```sh
virtualenv -p /usr/bin/python3.7 venv
source venv/bin/activate
pip install -r app/requirements.txt
```

Using Python 3.7 is preferable since that's what'll run on App Engine, but
anything at or above Python 3.5 or so is probably fine.

Run the local Django server from the `tools/pfif-tools/app` directory with this
command:

```sh
python manage.py runserver
```

### Emulating App Engine

For most development, running a normal local Django server is enough. However,
for certain work (e.g., if you're modifying `app.yaml`), you'll need to check
interactions with App Engine. For that, you can use the dev\_appserver tool, by
running this command from the `tools/pfif-tools` directory:

```sh
tools/gae run app
```

`dev\_appserver` will set up a virtual environment and install dependencies in
it on each run, which is inconvenient, so I don't recommend running this way for
development if you don't have to.
