#!/usr/bin/env python3

import yaml
import requests
import bs4
import urllib
import datetime
import re
import time
import logging
import sqlite3

global_header = {
    "User-Agent": "PostmanRuntime/7.37.3",
    "Accept": "*/*",
    "Accept-Encoding": "gzip, deflate, br",
}

db_name = "wechat.db"

def parse_config(file) :
    with open(file, 'r') as f:
        return yaml.safe_load(f)
    
def get_article(name, wait_time):
    index = 1
    result = []
    while True:
        logging.info(f"Get page {index}")
        page = requests.get(f'''https://weixin.sogou.com/weixin?query={urllib.parse.quote(name)}&type=2&page={index}''', headers=global_header)
        soup = bs4.BeautifulSoup(page.text, 'html.parser')
        items = soup.find_all(class_='txt-box')
        if len(items) == 0:
            break
        for item in items:
            timere = re.compile(r'\d{10,}')
            article = {
                'title': item.find('h3').text.strip(),
                'url': 'https://weixin.sogou.com' + item.find('a')['href'],
                'time': datetime.datetime.fromtimestamp(int(timere.findall(str(item.find(class_='s2')))[0])),
                'author': item.find(class_='all-time-y2').text,
                'description': item.find(class_='txt-info').text,
            }
            if article['author'] == name:
                logging.info(f"{article['title']}")
                result.append(article)
        index+=1
        time.sleep(wait_time)
    return result
    

def get_articles(wechat_config):
    queries = wechat_config['queries']
    wait_time = wechat_config['wait_time']
    result = []
    for name in queries:
        logging.info("Query: " + name)
        result.extend(get_article(name, wait_time))
    return result

def save_to_db(articles):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    for article in articles:
        cur.execute("INSERT INTO articles VALUES (?, ?, ?, ?, ?)", (article['title'], article['url'], article['time'], article['author'], article['description']))
    conn.commit()
    conn.close()

def get_new_articles(articles):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    for article in articles:
        cur.execute("SELECT * FROM articles WHERE title = ?", (article['title'],))
        if len(cur.fetchall()) == 0:
            yield article
    conn.close()

def init_db():
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS articles (title text, url text, time text, author text, description text)")
    conn.commit()
    conn.close()

def main():
    init_db()
    config = parse_config("config.yaml")
    logging.debug(config)
    wechat_config = config['wechat']
    articles = get_articles(wechat_config)
    new_articles = list(get_new_articles(articles))
    if len(new_articles) > 0:
        save_to_db(new_articles)
    logging.info("New articles: " + str(len(new_articles)))

if __name__=="__main__":
    logging.basicConfig(level=logging.DEBUG)
    main()