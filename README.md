### Google Scraper

This repo contains a scraper package to retrieve coordinates from a search string.
The code is using selenium to instantiate drivers which retrieves the coordinates from a google maps search

If the search string does not find a definitive candidate (i.e: Google maps returns a string), the code will select the top result from the returned list.

### Install Locally

run on your python environement

```bash
pip install git+https://github.com/Billy-Bat/google-scraper.git#egg=google_scraper
```

