import requests
from bs4 import BeautifulSoup
from multiprocessing.dummy import Pool as ThreadPool
from random import choice

import logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logging.getLogger("requests").setLevel(logging.WARNING)


# NOTE: The next two sections are for demo purposes only, they will be imported from modules
# this will be stored in proxies.py module
from random import choice
proxies = [
    {'host': '1.2.3.4', 'port': '1234', 'username': 'myuser', 'password': 'pw'},
    {'host': '2.3.4.5', 'port': '1234', 'username': 'myuser', 'password': 'pw'},
]
def check_proxy(session, proxy_host):

    response = session.get('https://canihazip.com/s')
    returned_ip = response.text
    if returned_ip != proxy_host:
        raise StandardError('Proxy check failed: {} not used while requesting'.format(proxy_host))
def random_proxy():
    resp = requests.get("https://gimmeproxy.com/api/getProxy?protocol=http&port=80&country=US")
    #resp = requests.get("http://pubproxy.com/api/proxy?limit=1&format=txt&http=true&country=US&type=http")
    #if resp.status_code == 200:
    #    return resp.content
    #return None
    resp = resp.json()
    return {'host':resp['ip'], 'port':resp['port'], 'protocol':resp['protocol']}
    #return choice(proxies)
# / end of proxies.py

# this will be stored in user_agents.py module

user_agents = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/600.8.9 (KHTML, like Gecko) Version/8.0.8 Safari/600.8.9',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36',
]
def random_user_agent():
    return choice(user_agents)
# / end of user_agents.py


def scrape_results_page(url):
    #import pdb;pdb.set_trace()
    proxy = random_proxy()  # will be proxies.random_proxy()

    while not proxy:
        proxy = random_proxy()
    session = requests.Session()
    session.headers = random_user_agent()  # will imported with "from user_agents import random_user_agent"
    session.proxies = {'http': "{protocol}://{host}:{port}/".format(**proxy)}
    #session.proxies = {'http': "http://{username}:{password}@{host}:{port}/".format(**proxy)}
    check_proxy(session, proxy['host'])  # will be proxies.check_proxy(session, proxy['host'])

    response = session.get(url)
    soup = BeautifulSoup(response.text, 'lxml')
    try:
        first_item_title = soup.find('h3', class_="lvtitle").text.strip()
        return first_item_title
    except Exception as e:
        print url
        logging.error(e, exc_info=True)
        return None


if __name__ == '__main__':
    page_numbers = range(1, 10)
    search_url = 'http://www.ebay.com/sch/Gardening-Supplies-/2032/i.html?_pgn='
    url_list = [search_url + str(i) for i in page_numbers]
    
    results = scrape_results_page(search_url+str(1))
    # Make the Pool of workers
    #pool = ThreadPool(8)
    # Open the urls in their own threads and return the results
    #results = pool.map(scrape_results_page, url_list)
    # Close the pool and wait for the work to finish
    #pool.close()
    #pool.join()
