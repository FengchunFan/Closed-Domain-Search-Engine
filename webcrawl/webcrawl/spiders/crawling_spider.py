#reference: https://www.youtube.com/watch?v=m_3gjHGxIJc

#compile line: scrapy crawl WebCrawler
#size check: stat -c "%s" output0.csv

import os
import csv
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor
from scrapy.exceptions import CloseSpider #stop spider under certain condition
#import pandas as pd

class WebCrawler(CrawlSpider):
    name = "WebCrawler" #identifier
    allowed_domains = ["www.ucr.edu"]
    handle_httpstatus_list = [404, 429]
    #seed.txt, to be modified
    start_urls = ["https://www.ucr.edu/"]
    keyword = "ucr" #school name

    #size limiter
    max_size = 10 * 1024 * 1024 #10MB
    #current_size = 0
    document_num = 0
    file_name = f"output{document_num}.csv"
    
    #crawl
    rules = (
        Rule(LinkExtractor(allow=keyword and "edu"), callback="parse"), 
    #    Rule(LinkExtractor(allow="edu"), callback="parse"),
    )

    #decide how to scrape the links
    def parse(self, response):
        #force return type to be text, avoid scrapy.exceptions.NotSupported: Response content isn't text, chatgpt generated code
        #content_type = response.headers.get('content-type', '').decode('utf-8').lower()
        #if 'text/html' not in content_type:
        #    return

        #specified by check source code for ucr webs
        title_plain = response.css('title::text').get()
        title_og = response.css('meta[property="og:title"]::attr(content)').get() 
        description_meta = response.css('meta[name="description"]::attr(content)').get()
        description_og = response.css('meta[property="og:description"]::attr(content)').get()
        url_og = response.css('meta[property="og:url"]::attr(content)').get()
        url_plain = response.url #url of current website
        
        if title_og is not None:
            title = title_og
        else:
            title = title_plain
        
        if description_og is not None:
            description = description_og
        else:
            description = description_meta

        if url_og is not None:
            url = url_og
        else:
            url = url_plain

        #as long as legit title and url
        if (title and description and url):
            yield{
               "title": title,
                "description": description,
                "url": url
            }
            '''
            data = {
                "title": title,
                "description": description,
                "url": url
            }
            df = pd.DataFrame([data])
            df.to_csv(self.file_name, mode='a', index=False, header=not os.path.isfile(self.file_name))
            '''
            data = [title, description, url]
            with open(self.file_name, mode='a', newline='') as file:
                writer = csv.writer(file)
                #writer.writerow([item.replace('\n', '') if item else None for item in data]) #keep everything in 1 page 1 row format
                writer.writerow([item.replace('\n', '') for item in data])
                file.close()
            
        #size checker, making sure each output contains only the limited amount of data
        if(os.path.isfile(self.file_name)):
            if(os.path.getsize(self.file_name) > self.max_size):
                print("reach size limit, size of output file: ", os.path.getsize(self.file_name)/1024/1024, "MB")
                self.document_num += 1
                self.file_name = f"output{self.document_num}.csv"
                #raise CloseSpider

        #if(self.document_num == 13):
        #    raise CloseSpider

        #reference: https://www.youtube.com/watch?v=-mkewdn9JdU&t=415s
        for link in response.css('a::attr(href)').getall():
            #if link.startswith('/') and self.keyword in link:
            if link.startswith('/'):
                yield response.follow(link,callback=self.parse)