from datetime import datetime

import scrapy


class FCCSpider(scrapy.Spider):
    name = "fcc"

    def start_requests(self):
        urls = ["https://fcc.report/FCC-ID/"]
        for url in urls:
            yield scrapy.Request(url=url, callback=self.parse)

    def parse(self, response):
        table = response.css("table.table")
        rows = table.css("tr")

        for row in rows:
            filing = {
                "company_name": row.css('td div[style="float: right;"]::text').get(),
                "final_action_date": row.css('td:nth-child(2) div[style="float: left;"]::text').get(),
            }

            label_element = row.css('td:last-child span.label')
            if label_element:
                filing["action_type"] = label_element.css('::text').get()
            else:
                filing["action_type"] = "UNKNOWN ACTION TYPE"

            href_links = row.css("td:nth-child(1) a::attr(href)")
            yield from response.follow_all(
                urls=href_links,
                callback=self.parse_application,
                cb_kwargs=dict(filing=filing),
            )

    def parse_application(self, response, filing):
        application_table = response.css("div.well table.table")
        application_rows = application_table.css("tr")

        items = {
            r.css("td:nth-child(1)::text").get(): r.css("td:nth-child(2)::text").get() for r in application_rows
        }

        yield filing | items | {"scrape_time": datetime.now()}
