import requests
import bs4
import pandas as pd
from datetime import datetime

debug = False


def get_jobs(soup):
    # Extract all job titles from the soup
    jobs = []
    elements = soup.find_all(name='a', attrs={'data-tn-element': 'jobTitle'})
    for element in elements:
        jobs.append(element['title'].strip())
    return(jobs)


def get_companies(soup, number_of_jobs):
    # Extract all company names from the soup
    companies = []
    spans = soup.find_all(name='span', attrs={'class': 'company'})
    if not spans:
        for company in range(number_of_jobs):
            companies.append('Company name not found.')

    else:
        for span in spans:
            companies.append(span.text.upper().strip())

    return(companies)


def get_locations(soup, number_of_jobs):
    # Extract all job locations from the soup
    locations = []
    spans = soup.findAll('span', attrs={'class': 'location'})
    if not spans:
        for location in range(number_of_jobs):
            locations.append('Location not found.')

    else:
        for span in spans:
            locations.append(span.text.strip())

    return(locations)


def get_summaries(soup, number_of_jobs):
    # Extract all job summaries from the soup
    summaries = []
    spans = soup.findAll('span', attrs={'class': 'summary'})
    if not spans:
        for summary in range(number_of_jobs):
            summaries.append('A summary was not found.')

    else:
        for span in spans:
            summaries.append(span.text.strip())

    return(summaries)


def get_ages(soup, number_of_jobs):
    # Extract the age of all job postings from the soup
    ages = []
    divs = soup.find_all(name='div', attrs={'class': 'result-link-bar'})
    if not divs:
        for age in range(number_of_jobs):
            ages.append('No age found.')

    else:
        for div in divs:
            span = div.find(name='span', attrs={'class': 'date'})
            if span is not None:
                ages.append(span.text.strip())

            else:
                ages.append('No age found.')

    return(ages)


def get_links(soup, number_of_jobs):
    # Extract all the job listing urls from the soup
    links = []
    elements = soup.find_all(name='a', attrs={'data-tn-element': 'jobTitle'})
    if not elements:
        for link in range(number_of_jobs):
            links.append('Link not found.')

    else:
        for element in elements:
            links.append('www.indeed.com' + str(element['href']))

    return(links)


def does_a_nextpage_exist(soup):
    # Check whether there exists another page to browse
    spans = soup.find_all(name='span', attrs={'class': 'np'})
    for span in spans:
        if 'Next' in span.text:
            return(True)
    return(False)


def get_nextpage_url(soup):
    # If another page exists, get the url
    div = soup.find(name='div', attrs={'class': 'pagination'})
    elements = div.find_all(name='a')
    nextpage_url = 'https://www.indeed.com/' + str(list(elements)[-1]['href'])
    return(nextpage_url)


def create_hyperlink(link):
    return '<a href="https://{}">{}</a>'.format(link, "Link")


def get_all_parameters_for_all_listings(url, max_pages):
    # Get all parameters from the soup and collect them in a dataframe
    response = requests.get(url)
    if debug:
        print(response.status_code)

    html = response.text
    soup = bs4.BeautifulSoup(html, 'html.parser')

    all_jobs = []
    all_companies = []
    all_locations = []
    all_summaries = []
    all_ages = []
    all_links = []

    page_counter = 1

    while True:
        currentpage_jobs = get_jobs(soup)
        all_jobs.extend(currentpage_jobs)
        number_of_jobs = len(currentpage_jobs)

        currentpage_companies = get_companies(soup, number_of_jobs)
        all_companies.extend(currentpage_companies)

        currentpage_locations = get_locations(soup, number_of_jobs)
        all_locations.extend(currentpage_locations)

        currentpage_summaries = get_summaries(soup, number_of_jobs)
        all_summaries.extend(currentpage_summaries)

        currentpage_ages = get_ages(soup, number_of_jobs)
        all_ages.extend(currentpage_ages)

        currentpage_links = get_links(soup, number_of_jobs)
        all_links.extend(currentpage_links)

        # Check to see if this is the last page; if not, move to the next page
        nextpage_exists = does_a_nextpage_exist(soup)
        if debug:
            print(nextpage_exists)

        if nextpage_exists is True and page_counter < max_pages:
            page_counter += 1
            if debug:
                print(page_counter)

            nextpage_url = get_nextpage_url(soup)
            if debug:
                print(nextpage_url)

            response = requests.get(nextpage_url)
            if debug:
                print(response.status_code)

            html = response.text
            soup = bs4.BeautifulSoup(html, 'html.parser')

        else:
            break

    if debug:
        print('Print # of jobs: {}'.format(str(len(all_jobs))))
        print('Print # of companies: {}'.format(str(len(all_companies))))
        print('Print # of locations: {}'.format(str(len(all_locations))))
        print('Print # of summaries: {}'.format(str(len(all_summaries))))
        print('Print # of ages: {}'.format(str(len(all_ages))))
        print('Print # of links: {}'.format(str(len(all_links))))

    # Set display options for HTML table
    pd.set_option('display.max_colwidth', 1500)
    pd.set_option('display.max_rows', 10000)

    df = pd.DataFrame(
                     {'Job Title': all_jobs,
                      'Company': all_companies,
                      'Location': all_locations,
                      'Job Summary': all_summaries,
                      'Age': all_ages,
                      'Link': all_links}
                     )

    # Re-order df columns for readability
    df = df[
            ['Job Title',
             'Link',
             'Company',
             'Location',
             'Age',
             'Job Summary']
           ]

    # Create hyperlinks
    df['Job Title'] = "<a href='https://" \
                      + df['Link'].astype(str) \
                      + "' target='_blank' >" \
                      + df['Job Title'].astype(str) \
                      + "</a>"

    # Clean up the dataframe + sort
    df = df.replace(r'\n', ' ', regex=True)
    df = df.sort_values('Company')
    return(df)


if __name__ == '__main__':
    # Output all job parameters for a given query to CSV

    search_q = 'analyst'
    search_l = 'Bay Area, CA'
    search_url = ('https://www.indeed.com/jobs?q={}&l={}'.format(search_q,
                                                                 search_l))

    
    


    if debug:
        print(search_url)

    df_all_parameters = get_all_parameters_for_all_listings(search_url)
    current_date = datetime.now()

    df_all_parameters.to_csv('{}_{}.csv'.format(
                              current_date.strftime('%Y-%m-%d'),
                              search_q.upper()))
