import numpy as np
import os

from PIL import Image
from wordcloud import WordCloud
from list_jobs import get_all_parameters_for_all_listings
from count_keywords import get_words_by_freq

debug = False

d = os.path.dirname(__file__)
static_path = os.path.abspath(os.path.join(d, '..', 'static'))
font_path = os.path.join(static_path, 'DIN_Condensed_Bold.ttf')

# Setup mask
with Image.open(os.path.join(static_path, 'images', 'spider-mask.png')) as img:
    new_image = Image.new('RGB', img.size, (255, 255, 255))
    new_image.paste(img, img)
    mask = np.array(new_image)


def generate_wordcloud(d_words):
    # Generate wordcloud in the shape of a spider
    wordcloud = WordCloud(font_path=font_path,
                          background_color='white',
                          max_words=3000,
                          mask=mask,
                          max_font_size=500,
                          random_state=42)

    wordcloud.generate_from_frequencies(d_words)
    return(wordcloud)


if __name__ == '__main__':
    # Build a search_url and get a dict containing words and their freq

    search_q = 'firefighter'
    search_l = 'Bay Area, CA'
    search_url = ('https://www.indeed.com/jobs?q={}&l={}'.format(search_q,
                                                                 search_l))

    print(search_url)

    df = get_all_parameters_for_all_listings(search_url)
    links = df['Link'].tolist()
    d_words = get_words_by_freq(links, None, 5)
    test_wc = generate_wordcloud(d_words)
    test_wc.to_file('test.png')
