"""
Python class to scrap data for a particular restaurant whose zomato link is given
"""

import re
import urllib
from urllib import parse
from bs4 import BeautifulSoup
from urllib.parse import urlparse
import urllib.request
from selenium import webdriver
from selenium.common.exceptions import *  
from bs4 import NavigableString
import sys
import json
import time

browser = None
try:
    browser = webdriver.Firefox()
except Exception as error:
    print(error)


class ZomatoRestaurant:
    def __init__(self, url):
        self.url = url
        print("opening")
        self.html_text = None
        try:
            browser.get(self.url)
            self.html_text = browser.page_source
            # self.html_text = urllib.request.urlopen(url).read().decode('utf-8')
            # self.html_text = requests.get(url).text
        except Exception as err:
            print(str(err))
            return
        else:
            print('Access successful.')

        self.soup = None
        if self.html_text is not None:
            self.soup = BeautifulSoup(self.html_text)




    def load_all_reviews(self):
        
        browser.implicitly_wait(7);
        elem = browser.find_element_by_class_name('load-more')
        
        while(elem.is_displayed()):
            print(elem.text);
            elem.click()
            browser.implicitly_wait(4)

            try:
                elem = browser.find_element_by_class_name('load-more')            
            except NoSuchElementException:
                print("No element found")
                break;

            
    

    def get_reviews(self):
        try:
            browser.get(self.url+'/reviews')
            self.review_html_text = browser.page_source 
        except Exception as err:
            print(str(err))
            return

        self.reviewSoup = BeautifulSoup(self.review_html_text)
        link = browser.find_element_by_xpath("//a[@data-sort='reviews-dd']");
        print("waaiting 15 s")
        time.sleep(15)
        # link.click();
        # action = webdriver.common.action_chains.ActionChains(browser)
        # action.move_to_element(link)
        # action.perform()

        print("clicking all review btn " + link.text);
        link.click()

        self.load_all_reviews();


        new_source = browser.execute_script("return document.body.innerHTML")
        print(new_source)
        new_soup = BeautifulSoup(new_source)

        reviews_body = new_soup.find_all('div' , attrs =  {"class" : "res-review-body"})
        reviews = [];
        for review_body in reviews_body:
            review = dict()
            review_text = review_body.find('div' , attrs = {"class" : "rev-text"}).text.strip()
            review_author = review_body.find('div' , attrs = {"class" : "header"}).text.strip()
            review_date = review_body.find('time').text.strip()

            review_text = " ".join(review_text.split()[1:])
            review_author = " ".join(review_author.split())

            review['text'] = review_text;
            review['author'] = review_author;
            review['date'] = review_date;

            reviews.append(review);
            print(review);

        return reviews;


    

    def scrap(self):
        if self.soup is None:
            return {}
        soup = self.soup
        rest_details = dict()

        name_anchor = soup.find("a", attrs={"class": "ui large header left"})
        if name_anchor:
            rest_details['name'] = name_anchor.text.strip()
        else:
            rest_details['name'] = ''

        rating_div = soup.find("div", attrs={"class": re.compile("rating-for")})
        if rating_div:
            rest_details['rating'] = rating_div.text.strip()[:-2]
        else:
            rest_details['rating'] = 'N'  # default

        contact_span = soup.find("span", attrs={"class": 'tel'})
        if contact_span:
            rest_details['contact'] = contact_span.text.strip()
        else:
            rest_details['contact'] = ''

        cuisine_box = soup.find('div', attrs={'class': 'res-info-cuisines clearfix'})
        rest_details['cuisines'] = []
        if cuisine_box:
            for it in cuisine_box.find_all('a', attrs={'class': 'zred'}):
                rest_details['cuisines'].append(it.text)

        geo_locale = soup.find("div", attrs={"class": "resmap-img"})
        if geo_locale:
            geo_url = geo_locale.attrs['data-url']
            parsed_url = urlparse(geo_url)
            geo_arr = str(urllib.parse.parse_qs(parsed_url.query)['center']).split(',')
            rest_details['geo_location'] = [re.sub("[^0-9\.]", "", geo_arr[0]), re.sub("[^0-9\.]", "", geo_arr[1])]
        if 'geo_location' not in rest_details:
            rest_details['geo_location'] = ['undefined', 'undefined']

        price_two_tag = soup.find('div', attrs={'class': 'res-info-detail'})
        if price_two_tag:
            price_two_tag = price_two_tag.find('span', attrs={'tabindex': '0'})
        if price_two_tag:
            rest_details['price_two'] = re.sub("[^0-9]", "", price_two_tag.text.strip())

        price_beer_tag = soup.find('div', attrs={'class': 'res-info-detail'})
        if price_beer_tag:
            price_beer_tag = price_beer_tag.find('div', attrs={'class': 'mt5'})
        if price_beer_tag:
            rest_details['price_beer'] = re.sub("[^0-9]", "", price_beer_tag.text.strip())

        res_info = []
        for it in soup.findAll("div", attrs={'class': 'res-info-feature-text'}):
            try:
                res_info.append(it.text.strip())
            except NavigableString:
                pass
        rest_details['facility'] = res_info

        week_schedule = soup.find("div", attrs={"id": "res-week-timetable"})
        data = []
        if week_schedule:
            time_table = week_schedule.table
            rows = time_table.findAll('tr')
            for row in rows:
                cols = row.find_all('td')
                cols = [ele.text.strip() for ele in cols]
                data.append([ele for ele in cols if ele])
        rest_details['timetable'] = data

        collection_box = soup.find('div', attrs={'class': 'ln24'})
        rest_details['featured_collections'] = []
        if collection_box:
            for it in collection_box.find_all('a', attrs={'class': 'zred'}):
                rest_details['featured_collections'].append(it.text.strip())

        address_div = soup.find("div", attrs={"class": "resinfo-icon"})
        if address_div:
            rest_details['address'] = address_div.span.get_text()
        else:
            rest_details['address'] = ""

        known_for_div = soup.find("div", attrs={'class': 'res-info-known-for-text mr5'})
        if known_for_div:
            rest_details['known_for'] = known_for_div.text.strip()
        else:
            rest_details['known_for'] = ''

        rest_details['what_people_love_here'] = []
        for div in soup.find_all("div", attrs={'class': 'rv_highlights__section pr10'}):
            child_div = div.find("div", attrs={'class': 'grey-text'})
            if child_div:
                rest_details['what_people_love_here'].append(child_div.get_text())


        rest_details['reviews'] = self.get_reviews()

        return rest_details


if __name__ == '__main__':
    if browser is None:
        sys.exit()
    out_file = open("zomato_chandigarh_2.json", "a")
    with open('chandigarh_restaurant_details_2.txt', 'r', encoding="utf-8") as f:
        for line in f:
            zr = ZomatoRestaurant(line)
            json.dump(zr.scrap(), out_file)
            out_file.write('\n')
    out_file.close()
    browser.close()
