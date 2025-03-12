@echo off
pip install scrapy
cd /d %~dp0
cd webcrawl
scrapy crawl WebCrawler
pause