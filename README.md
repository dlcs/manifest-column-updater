# Manifest Column Updater

This project updates the DLCS with manifests from the presentation database.

## Running locally

1. move to the `src` folder

```powershell
cd src
```

2. create a venv

```powershell
python -m venv .venv
```

3. activate the venv (using the terminal specific script)

```powershell
.venv\Scripts\Activate.ps1
```

4. install the modules from requirements

```powershell
pip install requirements.txt -r
```

5. create a `.env` file using the `.env.dist` file
6. run the script

```powershell
python -m .\manifest-column-updater.py
```

## Environment variables

| name                           | description                                                                                                | type     |
|--------------------------------|------------------------------------------------------------------------------------------------------------|----------|
| DRY_RUN                        | This will pull details from presentation, but won't actually update protagonis                             | boolean  |
| CONNECTION_TIMEOUT             | How long the connection to the presentation database will last before timing out                           | integer  |
| PRESENTATION_CONNECTION_STRING | The connection string used to talk to the presentation database                                            | string   |
| HIGH_WATER_MARK                | A timestamp denoting the earliest point in time that data will be retrieved from the presentation database | datetime |
| PROTAGONIST_BASE_URL           | The base URL for the protagonist API                                                                       | string   |
| DLCS_API_AUTH                  | base64 encoded credentials for talking to the protagonist API. NOTE: these should be admin                 | string   |
| EXIT_ON_ERROR                  | If an error is detected when talking to protagonist, the application will exit when true                   | boolean  |

## Freezing dependencies

if using powershell, the dependencies can be frozen using the following command:

```powershell
pip freeze -l | Out-File requirements.txt -Encoding UTF8
```
