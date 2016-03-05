edline-scraper
==============
Crawl our Edline school site, download HTML, PDF and image files, and upload them to Google Drive.
Uses scrapy tool.

This is the first part of a pipeline that will use the gdrive-static-site project.

Invoke the crawler with:

     scrapy crawl gdrive -o items.json -a max_requests=1000
