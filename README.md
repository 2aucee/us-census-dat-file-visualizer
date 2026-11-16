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

The app recognizes `sep19pub.csv`, `sep21pub.csv`, `sep23pub.csv`, and `sep23pub.dat`. Choose a preview size of 100, 500, or 1,000 rows. For recognized CPS CSVs, only the selected variable and optional weight are read across the full file instead of loading every column into memory for analysis. Common CPS supplement variables and documented response codes are shown with plain-English labels. CPS special value `-1` is displayed as `N/A`; `-2` (don't know), `-3` (refused), and `-9` (no answer) are described with their original codes in parentheses. Other undocumented values are retained rather than guessed. Numeric fields offer histograms, box plots, and summary statistics; coded numeric fields can also be viewed as categories. Categorical fields offer bar and donut charts. You can optionally select a numeric weight field for descriptive weighted summaries. Weighted values are not a substitute for CPS survey-design variance estimation and do not account for replicate weights.

The bundled `sep23pub.dat` positions and response labels come from the Census Bureau's [September 2023 CPS technical documentation](https://www2.census.gov/programs-surveys/cps/techdocs/cpssep23.pdf). Labels for the September 2019 and 2021 supplements are based on the Census Bureau's [September 2019](https://www2.census.gov/programs-surveys/cps/techdocs/cpssept19.pdf) and [September 2021](https://www2.census.gov/programs-surveys/cps/techdocs/cpssept21.pdf) CPS technical documentation, especially Attachment 7 (Supplement Record Layout). Undocumented positive values remain visible as their original value; the standard negative special codes are described without replacing their code.

## FBLA Data Analysis workspace

Choose **FBLA social impact analysis** to compare the Census Civic Engagement and Volunteering (CEV) supplements. Upload any combination of the official `sep17pub.dat`, `sep17pub.dat.gz`, or `sep17pub.zip` release and `sep19pub.csv`, `sep21pub.csv`, and `sep23pub.csv`. The 2017 data is fixed-width; the other supported releases are delimited CSV. The app extracts only the analysis fields it needs and supports one file per survey year.

The workspace provides weighted year-by-year estimates for volunteering, donations over $25, and civic participation; three topic trend charts plus an age-group volunteering chart; a cautious candidate-priority prompt; and downloads for the labeled respondent data and weighted estimates. The larger respondent export is generated only when requested. It includes readable response descriptions with original codes in parentheses, survey year, broad age group, and survey weight, and omits Census identifiers.

Rates use the supplement nonresponse weight (`PWNRWGT`) among records with a valid yes/no response and positive weight. The table shows both unweighted valid-response counts and weighted bases. `PES17`/`PES18` represent donations over $25 rather than all giving, and informal volunteering (`PES16A`) follows survey routing. Not-in-universe and other nonresponse values are excluded from yes/no denominators. These descriptive estimates do not include CPS replicate-weight variance calculations, confidence intervals, or significance tests. Survey years are repeated cross-sections, not a panel of the same people; changes do not establish cause and effect. Review each year's Census documentation for question wording, response routing, and comparability before presenting conclusions.

The official source data and documentation links appear in the workspace. The 2017 fixed-width layout is based on the Census Bureau's [September 2017 CPS technical documentation](https://www2.census.gov/programs-surveys/cps/techdocs/cpssep17.pdf); the official data releases can be found through the Census Bureau's annual [2017](https://www2.census.gov/programs-surveys/cps/datasets/2017/supp/), [2019](https://www2.census.gov/programs-surveys/cps/datasets/2019/supp/), [2021](https://www2.census.gov/programs-surveys/cps/datasets/2021/supp/), and [2023](https://www2.census.gov/programs-surveys/cps/datasets/2023/supp/) CPS supplement directories.

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
