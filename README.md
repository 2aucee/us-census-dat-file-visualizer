# Census Data Explorer

A local Streamlit app and Jupyter research starter for exploring Census Bureau text files. The app supports delimited files, fixed-width records when you supply the official layout, and the September 2023 CPS Civic Engagement and Volunteering `sep23pub.dat` file with its bundled Census-documented record layout.

## Set up on Windows

Install Python 3.10 or later, then open this folder in VS Code and run these commands in PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m streamlit run app.py
```

Streamlit opens the website in your browser. Upload a `.dat`, `.txt`, `.csv`, or `.tsv` file. `.dat` files default to fixed-width mode. The known `sep23pub.dat` file is recognized by name and parsed with the included official field positions. For other fixed-width files, paste a CSV layout with `name,start,end` columns; positions are one-based and inclusive as in most record-layout documentation.

The app recognizes `sep23pub.dat`, `sep23pub.csv`, and `sep21pub.csv`. Delimited files are previewed at 100 rows and, when you explore a variable, only that field and an optional weight are read across the full file instead of loading every column into memory. Common CPS supplement variables and documented response codes are shown with plain-English labels. CPS special value `-1` is displayed as `N/A`; `-2` (don't know), `-3` (refused), and `-9` (no answer) are described with their original codes in parentheses. Other undocumented values are retained rather than guessed. The app shows missing-value and field summaries, numeric distributions/statistics, and category counts. You can optionally select a numeric weight field for descriptive weighted summaries. Weighted values are not a substitute for CPS survey-design variance estimation and do not account for replicate weights.

The bundled `sep23pub.dat` positions and response labels come from the Census Bureau's [September 2023 CPS technical documentation](https://www2.census.gov/programs-surveys/cps/techdocs/cpssep23.pdf). Undocumented positive values remain visible as their original value; the standard negative special codes are described without replacing their code.

## Jupyter notebook

Launch Jupyter with:

```powershell
.\.venv\Scripts\python.exe -m jupyter notebook
```

Open `notebooks/research_starter.ipynb`. Place your file in `data\sep23pub.dat` and add the official record layout before loading it. Check the Census codebook for value labels, weights, and survey methodology before interpreting results.

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
