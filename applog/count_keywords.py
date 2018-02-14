import requests
import bs4
import operator
import os

from list_jobs import get_all_parameters_for_all_listings
from pprint import pprint

debug = False

d = os.path.dirname(__file__)
static_path = os.path.abspath(os.path.join(d, '..', 'static'))

with open(os.path.join(static_path, 'COMMON.txt')) as f1:
    COMMON = set(line.strip() for line in f1)

with open(os.path.join(static_path, 'EN_DICT.txt')) as f2:
    EN_DICT = set(line.lower().strip() for line in f2)


def get_text_all(links, max_links):
    # Provided a list of urls, get all text from each url

    text_by_link = []
    success_counter = 0
    failure_counter = 0

    if debug:
        total_number_of_links = len(links)
        print('Out of {} links in total...'.format(total_number_of_links))

    for link in links:
        if 'http' in link:
            url = link
        else:
            url = 'https://{}'.format(link)

        try:
            response = requests.get(url, timeout=3)
            html = response.text
            soup = bs4.BeautifulSoup(html, 'html.parser')
            all_text = soup.findAll(text=True)
            page_text = all_text
            text_by_link.append(page_text)
            success_counter = success_counter + 1
            if success_counter == max_links:
                break

        except:
            if debug:
                print('{} did not work for some reason.'.format(url))
            failure_counter = failure_counter + 1
            continue

    if debug:
        print('{} were crawled successfully.'.format(success_counter))

    return(text_by_link)


def get_text_from_link(link):
    # Provided a single url, get all text

    if 'http' in link:
        url = link
    else:
        url = 'https://' + link

    try:
        response = requests.get(url)
        html = response.text
        soup = bs4.BeautifulSoup(html, 'html.parser')
        all_text = soup.findAll(text=True)
        page_text = all_text

    except:
        if debug:
            print('{} did not work for some reason.'.format(url))

    return(page_text)


def clean(word):
    # Removes punctuation and special chars from a specified string
    clean_word = ''.join(e for e in word.lower() if e.isalnum())
    return(clean_word)


def filter_by_relevance(words):
    # Exclude specific words and ensure all words are dict terms
    relevant_list = []

    with open(os.path.join(static_path, 'CUSTOM.txt')) as f3:
        CUSTOM = set(line.strip() for line in f3)

    for word in words:
        if len(word) < 12 and len(word) > 3 and \
           any(char.isdigit() for char in word) is False:
            if word not in COMMON and word not in CUSTOM:
                if word in EN_DICT:
                    relevant_list.append(word)

    return(relevant_list)


def split_by_word(text_by_link):
    # Split chunks into words
    all_words = []
    for link_text in text_by_link:
        for text in link_text:
            words_in_text = text.split()
            for word in words_in_text:
                clean_word = clean(word)
                all_words.append(clean_word)

    return(all_words)


def count_unique_words(list_of_words):
    # Create a dictionary containing a list of words and their relative freq
    unique_words = {}
    for word in list_of_words:
        if word not in unique_words:
            unique_words[word] = 1
        else:
            unique_words[word] = unique_words.get(word) + 1

    return(unique_words)


def get_words_by_freq(links, sort_type, max_links):
    # Provided a search_string_url, return a dictionary containing words-b-freq
    all_words = split_by_word(get_text_all(links, max_links))
    relevant_words = filter_by_relevance(all_words)
    d_words = count_unique_words(relevant_words)

    if sort_type is 'key':
        words_by_frequency = sorted(d_words.items(),
                                    key=operator.itemgetter(0),
                                    reverse=True)

    elif sort_type is 'value':
        words_by_frequency = sorted(d_words.items(),
                                    key=operator.itemgetter(1),
                                    reverse=True)

    else:
        words_by_frequency = d_words

    if debug:
        print('Within the dictionary, '
              'there are {} unique words.'.format(len(d_words)))

        pprint(words_by_frequency)

    return(words_by_frequency)


if __name__ == '__main__':

    # Build search_url and get a dataframe containing all associated links
    search_q = 'firefighter'
    search_l = 'Bay Area, CA'
    search_url = ('https://www.indeed.com/jobs?q={}&l={}'.format(search_q,
                                                                 search_l))

    print(search_url)

    df = get_all_parameters_for_all_listings(search_url)
    links = df['Link'].tolist()
    get_words_by_freq(links, None, 5)
