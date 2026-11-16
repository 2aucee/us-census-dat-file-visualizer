# Census Data Explorer

A Streamlit app for students to open and explore Census Bureau CSV files. Uploads are read in memory and aren't saved by the app.

## Set up on Windows

Install Python 3.10 or later, then open this folder in VS Code and run these commands in PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Streamlit opens the website in your browser. Upload a `.csv` file to see its table preview and explore a column with a chart or summary.

Choose a preview size of 100, 500, or 1,000 rows. Common CPS files (`sep19pub.csv`, `sep21pub.csv`, and `sep23pub.csv`) show readable variable and response labels, including `N/A` for not-in-universe values. Other CSV files are shown with their original headers and values. The table keeps the imported data visible; charts and summaries are available when you choose a column.

Common CPS code labels use the Census Bureau's [September 2019](https://www2.census.gov/programs-surveys/cps/techdocs/cpssept19.pdf), [September 2021](https://www2.census.gov/programs-surveys/cps/techdocs/cpssept21.pdf), and [September 2023](https://www2.census.gov/programs-surveys/cps/techdocs/cpssep23.pdf) documentation. Undocumented values are left unchanged rather than guessed.

## Test

```powershell
.\.venv\Scripts\python.exe -m pytest
```

## Data handling

The app processes the uploaded file in memory and does not save it. When deployed to Streamlit Community Cloud, the uploaded file is sent to that hosted app while you use it. Dataset files and common exports are ignored by Git. Do not commit the Census data or any sensitive files.

## Deploy to Streamlit Community Cloud

After pushing this repository to GitHub, sign in at [share.streamlit.io](https://share.streamlit.io), choose **Create app**, select this repository and the `main` branch, and set the app file to `app.py`. Streamlit will build the app from `requirements.txt` and provide a hosted URL. The app code is public because this repository is public; anyone with access to the hosted app can upload a file to it.

## GitHub

Initialize a repository locally with:

```powershell
git init
git add .
git commit -m "Create Census data explorer"
```

Create an empty GitHub repository, then connect and push:

```powershell
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/us-census-dat-file-visualizer.git
git push -u origin main
```

Check `git status` before pushing to confirm that no dataset has been staged.
