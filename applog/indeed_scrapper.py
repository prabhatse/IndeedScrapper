
import bs4
import requests
import pickle
import time

debug = True

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
        job_url = 'https://www.indeed.com/viewjob?' + urls[1]

        job_soup = get_soup(job_url)

        job_description = job_soup.find(name='span', attrs={'id': 'job_summary'})
        
        links.append({
            'title':job_title, 
            'url':job_url,
            'location': location,
            'duration': duration,
            'job_description': job_description
            })    
    return(links)


def get_companies_links(soup):
    links = {}
    elements = soup.find_all(name='a', attrs={'data-tn-element': 'title-link'})
    for element in elements:
        links[str(element.text).lower()] = 'www.indeed.com'+str(element['href'])
    elements = soup.find_all(name='a', attrs={'data-tn-element': 'searchResult'})
    for element in elements:
        links[str(element.text).lower()] = 'www.indeed.com'+str(element['href'])
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

def get_soup(search_url):
    response = requests.get(search_url)
    if debug:
        print response.status_code
    html = response.text
    soup = bs4.BeautifulSoup(html, 'html.parser')    
    return soup

def get_company_job_links(link):   
    page = "https://"+link+"/jobs"
    jobs = []
    while page:
        time.sleep(1)
        soup = get_soup(page)
        job_links = get_jobs_links(soup)
        jobs.append(job_links+[])
        page = does_a_nextpage_exist(soup)
    return jobs

def get_indeed_company_links():
    file = 'companies_list.pkl'
    pick_doc = open(file, 'rb')
    companies = pickle.load(pick_doc)
    pick_doc.close()
    companies_link = {}
    search_url = "https://www.indeed.com/cmp?q=" #Company name
    for company in companies:
        time.sleep(2)
        companies_link[str(company)] = get_companies_link(get_soup(search_url+company))    
    return companies_link   

if __name__ == '__main__':  
    #file = 'refined_companies_link.pkl'
    #pickle.dump(companies_link, open(file, 'wb'))
    #companies_link = pickle.load(open(file, 'rb'))

    #comp_data = {key: companies_link[key] for key in companies_link.keys() if len(companies_link[key])}
    
    companies_link = {'Trustpilot': 'www.indeed.com/cmp/Trustpilot'}
    jobs_list_link = {}
    
    import pdb;pdb.set_trace()
    for company, link in companies_link.items():
        jobs_list_link[company] = get_company_job_links(link)

    file = 'refined_jobs.pkl'
    pickle.dump(jobs_list_link, open(file, 'wb'), protocol=2)

    print jobs_list_link










    












