# Closed Domain Search Engine with theme of eduational websites

1) Use python scrapy to crawl selected Education websites (sites ends with .edu)

    Scrapy crawling command: "scrapy crawl <crawler_name>"

    Run webcrawl.sh for terminal or run.bat for windows.

2) Index the data with Pylucene, and use Python Flask for the user interface

    Only the content body will be indexed, similarity checker is default tf-idf, retrieval number is top 10

    Use run.py to run step 2 and 3 (Make sure environment capable with Pylucene)

    Use online.sh to make the web accessible on other device through specified port

##
Referenced sources:

https://www.youtube.com/watch?v=m_3gjHGxIJc

https://docs.scrapy.org/en/latest/

https://scrapeops.io/python-scrapy-playbook/

https://www.freecodecamp.org/news/how-to-build-a-web-application-using-flask-and-deploy-it-to-the-cloud-3551c985e492/

https://flask.palletsprojects.com/en/0.12.x/quickstart/#rendering-templates

https://lucene.apache.org/core/2_9_4/queryparsersyntax.html

unsolvable issue:

https://github.com/scrapy/scrapy/issues/3321
