# tweescrapy

### Organisation:
- `twitter_bookmark_scrape.ipynb`: Notebook containing execution code. Comments should help navigate
- `tweescrapy.py`: backend code
    
### Installation:
2. Download both files and put into a folder which you can access with Jupyter

3. Install any uninstalled dependencies:
    - selenium
    - numpy
    - pandas

4. Setup selenium executable
    - download the appropriate webdriver executable (for your Chrome version and OS) from here: https://chromedriver.chromium.org/downloads

    - Once downloaded and unzipped, put this executable into the same folder as this webscraper code and then add the full filepath to this executable to the `driver_path` variable in the notebook.

6. To run, open the Jupyter notebook and follow the instructions. Output should be a dataframe containing your bookmarked tweets and threads (this will take a little while as the scraper navigates through the tweets/threads). Note that currently only posts by the original author are included.
