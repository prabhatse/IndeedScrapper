from flask import Flask, render_template, flash, request
from datetime import datetime
import os

import applog.list_jobs as jobs
import applog.count_keywords as keywords
import applog.generate_wordcloud as cloud

app = Flask(__name__)

d = os.path.dirname(__file__)
static_path = os.path.abspath(os.path.join(d, 'static', 'images', 'spiders'))


@app.route('/')
def homepage():
    flash('flash test')
    return render_template('main.html')


@app.route('/about/')
def about():
    return render_template('about.html')


@app.route('/search-results/', methods=['GET'])
def results():
    render_template('loader.html')
    search_q = request.args.get('q')
    search_l = request.args.get('l')
    max_pages = int(request.args.get('pages'))
    search_url = ('https://www.indeed.com/jobs?q={}&l={}'.format(search_q,
                                                                 search_l))

    # Get primary dataframe
    df = jobs.get_all_parameters_for_all_listings(search_url, max_pages)
    results_returned = len(df)
    flash('{} result(s) shown.'.format(
          results_returned))

    # Get dictionary of words by frequency
    words_by_frequency = keywords.get_words_by_freq(df['Link'].tolist(),
                                                    None,
                                                    100)

    # flash(words_by_frequency)

    # Create a unique name for dynamically generated spider_png
    current_dt = datetime.now()
    spider_name = '{}_{}.png'.format(current_dt.strftime('%Y-%m-%d'),
                                     search_q.strip())

    png_path = os.path.join(static_path, spider_name)

    # If the PNG does not already exist, then generate new wordcloud
    if os.path.exists(png_path) is False:
        wordcloud = cloud.generate_wordcloud(words_by_frequency)
        wordcloud.to_file(png_path)

    # Clean up the table to be displayed
    del df['Link']
    table = df.to_html(classes='table table-hover',
                       index=False,
                       escape=False)

    return render_template('results.html', TABLE=table, PNG=spider_name)


@app.route('/loading/')
def loader():
    return render_template('loader.html')


if __name__ == '__main__':
    app.run()
