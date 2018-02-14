import bs4
import requests
import pickle
import time
import redis
from random import choice
from celery.contrib import rdb
import string

TASK_CONFIGS = {
  'themuse_entry_level_job_url' : 'https://api-v2.themuse.com/jobs?level=Internship&level=Entry Level&company=', 
  'themuse_all_level_job_url' : 'https://api-v2.themuse.com/companies?page=',
  'themuse_company_url' : 'https://api-v2.themuse.com/companies?page=',
  'indeed_company_links_file': 'refined_companies_link.pkl',
  'themuse_companies_file' : 'companies.pkl',
  'indeed_view_jobs' : 'https://www.indeed.com/viewjob?',
  'indeed_company_url' : 'https://www.indeed.com',
  'indeed_company_search_url' : 'https://www.indeed.com/cmp?q=',
  'indeed_company_file' : 'refined_companies_link.pkl',

  'skills_keywords_file' : 'skills2.pkl',
  'search_string' : 'yearsexperience|yrsexperience|yearexperience|experienceof|\
            ofexperience|experiencein|experienced|senior|minimumexperience|yrsexperience',
  'search_delms' : ["proficiency","proficient","strong","excellent","expert","expertise","minimum"],
  'search_delms_2' : ["experience","proficiency","minimum","recent","expertise","proficient","strong","excellent"],
}

debug = True

user_agents = [
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_5) AppleWebKit/600.8.9 (KHTML, like Gecko) Version/8.0.8 Safari/600.8.9',
    'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.101 Safari/537.36',
    "Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_3; en-us; Silk/1.1.0-80) AppleWebKit/533.16 (KHTML, like Gecko) Version/5.0 Safari/533.16 Silk-Accelerated=true",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_8) AppleWebKit/537.13+ (KHTML, like Gecko) Version/5.1.7 Safari/534.57.2",
    "Mozilla/5.0 (X11; Ubuntu; Linux i686; rv:15.0) Gecko/20100101 Firefox/15.0.1",
    "Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0)",
    "Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; ARM; Trident/6.0)",
    "Mozilla/5.0 (Windows; U; Win 9x 4.90; en-GB; rv:1.8.1.1) Gecko/20061204 Firefox/2.0.0.1",
    "Mozilla/5.0 (X11; U; SunOS sun4u; en-US; rv:1.6) Gecko/20040503",
    "Mozilla/5.0 (X11; CrOS i686 0.12.433) AppleWebKit/534.30 (KHTML, like Gecko) Chrome/12.0.742.77 Safari/534.30",
]
def random_user_agent():
    return choice(user_agents)

def check_proxy(session, proxy_host):
    response = session.get('https://canihazip.com/s')
    returned_ip = response.text
    print(returned_ip +" "+proxy_host)
    if returned_ip != proxy_host:
        return False
    else:
        return True

def random_proxy():
    resp = requests.get("https://gimmeproxy.com/api/getProxy?protocol=http&country=US")
    try:
        resp = resp.json()
        return {'host':resp['ip'], 'port':resp['port'], 'protocol':resp['protocol']}
    except Exception as e:
        return {'host':'', 'port':'', 'protocol':''}
        

def does_a_nextpage_exist(soup):
    # Check whether there exists another page to browse
    nexts = soup.find_all(name='a', attrs={'data-tn-element': 'next-page'})
    if len(nexts):
        if 'Next' in nexts[0].text:
            return nexts[0]['href']
    return None


def get_jobs_links(soup):
    # Extract all the job listing urls from the soup
    links = []
    elements = soup.find_all(name='li', attrs={'class': 'cmp-section cmp-job-entry'})

    for element in elements:
        loc_dur  = element.find_all(name='div', attrs={'class': 'cmp-note'})
        location = loc_dur[0].text 
        duration = loc_dur[1].text
        job_detail = element.find(name='a', attrs={'class': 'cmp-job-url'})
        job_title = job_detail.text
        urls = str(job_detail['href']).split('?')
        if len(urls) < 2:
            continue
        job_url = TASK_CONFIGS['indeed_view_jobs'] + urls[1]
        apply_url = TASK_CONFIGS['indeed_company_url']+str(job_detail['href'])
        job_key = urls[1].split('&')[0][3:]
        job_soup = get_soup(job_url)
        job_description = job_soup.find(name='span', attrs={'id': 'job_summary'})
        links.append({
            'title':job_title, 
            'apply_url':apply_url,
            'location': str(location),
            'job_description': str(job_description),
            'id': 'indeed-'+job_key,
            'date_created': str(duration),
            'job_category': '',
            'experience_level': '',
            })    
    return(links)


def get_companies_links(soup):
    links = {}
    elements = soup.find_all(name='a', attrs={'data-tn-element': 'title-link'})
    for element in elements:
        links[str(element.text).lower()] = 'https://www.indeed.com'+str(element['href'])
    elements = soup.find_all(name='a', attrs={'data-tn-element': 'searchResult'})
    for element in elements:
        links[str(element.text).lower()] = 'https://www.indeed.com'+str(element['href'])
    return links

def refind_companies_link(comp_data):
    refined = {}
    for key, val in comp_data.items():
        key_lower = key.lower()
        found = False
        if not val.get(key_lower):
            for k, v in val.items():
                if key_lower in k:
                    refined[key] = v
                    break
        else:
            refined[key] = val.get(key_lower)
    return refined

def refine_company_links(key,data):
    key_lower = key.lower()
    if not data.get(key_lower):
        for k, v in data.items():
            if k.find(key_lower) == 0:
                return v
                break
    else:
        return data.get(key_lower)

def get_working_proxy():
    reds = redis.Redis()
    last_used_proxy = None
    if not reds:
        pass
    else:
        last_used_proxy = reds.get("last_indeed_proxy")
    
    proxy = None
    if last_used_proxy:
        proxy = eval(last_used_proxy)
    if not proxy:
        proxy = random_proxy()
    i = 0
    while proxy and i < 20:
        i += 1
        session = requests.Session()
        session.headers = random_user_agent()
        session.proxies = {'https':'{protocol}://{host}:{port}/'.format(**proxy)}
        try:
            if check_proxy(session, proxy['host']):
                if reds:
                    reds.set("last_indeed_proxy", proxy)
                return session
        except Exception as e:
            pass
        proxy = random_proxy()
    return None 
def get_soup(search_url):
    #rdb.set_trace()
    session = get_working_proxy()
    if not session:
        return
    try:
        response = session.get(search_url)
        #response = requests.get(search_url)
        if debug:
            print response.status_code
        html = response.text
        soup = bs4.BeautifulSoup(html, 'html.parser')    
        return soup        
    except Exception as e:
        return ""


def get_company_job_links(link):   
    page = "https://"+link+"/jobs"
    jobs = []
    count = 0
    while page:
        soup = get_soup(page)
        job_links = get_jobs_links(soup)
        jobs.extend(job_links)
        page = does_a_nextpage_exist(soup)
        time.sleep(1)
        #break
    return jobs

def get_indeed_company_link(company):
    if len(company):
        search_url = TASK_CONFIGS['indeed_company_search_url'] #Company name
        data = get_companies_links(get_soup(search_url+company))
        return refine_company_links(company, data)
    return None

def does_nextpage_exist_in_cmpsearch(soup):
    # Check whether there exists another page to browse
    nexts = soup.find_all(name='a', attrs={'data-tn-element': 'next-link'})
    if len(nexts):
        if 'Next' in nexts[0].text:
            return nexts[0]['href']
    return None


def get_indeed_companies_list(company):
    companies = {}
    page = TASK_CONFIGS['indeed_company_search_url'] + company
    while page:
        soup = get_soup(page)
        data = get_companies_links(soup)
        companies.update(data)
        page = does_nextpage_exist_in_cmpsearch(soup)
    return companies

def get_indeed_company_links_from_pkl():
    file = 'companies_list.pkl'
    pick_doc = open(file, 'rb')
    companies = pickle.load(pick_doc)
    pick_doc.close()
    companies_link = {}
    search_url = TASK_CONFIGS['indeed_company_search_url'] #Company name
    for company in companies:
        time.sleep(2)
        companies_link[str(company)] = get_companies_links(get_soup(search_url+company))    
    return companies_link   

def update_indeed_link_pickle(file, companies):
    try:
        pickle.dump(companies,open(file, 'wb'), protocol=2)
    except Exception as e:
        pass

def find_indeed_company_link(company):
    file = TASK_CONFIGS['indeed_company_file']
    companies_link = pickle.load(open(file, 'rb'))
    company_lower = company.lower()
    for company in companies_link.keys():
        if company_lower == company.lower():
            return companies_link[company]
    link = get_indeed_company_link(company)
    if link and len(link):
        companies_link[company] = link
        update_indeed_link_pickle(file, companies_link)
        return link
    return None

if __name__ = "__main__":

    companies = {}
    
    for c1 in string.ascii_lowercase:
        for c2 in string.ascii_lowercase:
            data =  get_indeed_companies_list(c1+c2)