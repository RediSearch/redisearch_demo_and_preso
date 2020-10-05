from flask import Flask, render_template, request, redirect
from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import Navbar, View
from redisearch import AutoCompleter, Suggestion, Client, Query, aggregation, reducers, IndexDefinition, TextField, NumericField, TagField

from os import environ

import redis

import json
import csv
import string

app = Flask(__name__)
bootstrap = Bootstrap()

if environ.get('REDIS_SERVER') is not None:
   redis_server = environ.get('REDIS_SERVER')
else:
   redis_server = 'localhost'

if environ.get('REDIS_PORT') is not None:
   redis_port = int(environ.get('REDIS_PORT'))
else:
   redis_port = 6379

if environ.get('REDIS_PASSWORD') is not None:
   redis_password = environ.get('REDIS_PASSWORD')
else:
   redis_password = ''

client = Client(
   'fortune500',
   host=redis_server,
   password=redis_password,
   port=redis_port
   )
ac = AutoCompleter(
   'ac',
   conn = client.redis
   )



nav = Nav()
topbar = Navbar('',
    View('Home', 'index'),
    View('Aggregations', 'show_agg'),
    View('CEO Search', 'search_ceo'),
    View('Tag Search', 'search_tags'),
)
nav.register_element('top', topbar)

def agg_by(field):
   ar = aggregation.AggregateRequest().group_by(field, reducers.count().alias('my_count')).sort_by(aggregation.Desc('@my_count'))
   return (client.aggregate(ar).rows)

def search_data(company):
   j = client.search(Query(company).limit_fields('title').verbatim()).docs[0].__dict__
   del j['id']
   del j['payload']
   return(j)

def load_data():
    definition = IndexDefinition(
            prefix=['fortune500:'],
            language='English',
            score_field='title',
            score=0.5
            )
    client.create_index(
            (
                TextField("title", weight=5.0),
                TextField('website'),
                TextField('company'),
                NumericField('employees', sortable=True),
                TextField('industry', sortable=True),
                TextField('sector', sortable=True),
                TextField('hqcity', sortable=True),
                TextField('hqstate', sortable=True),
                TextField('ceo'),
                TextField('ceoTitle'),
                NumericField('rank', sortable=True),
                NumericField('assets', sortable=True),
                NumericField('revenues', sortable=True),
                NumericField('profits', sortable=True),
                NumericField('equity', sortable=True),
                TagField('tags'),
                TextField('ticker')
                ),        
        definition=definition)

    with open('./fortune500.csv', encoding='utf-8') as csv_file:
       csv_reader = csv.reader(csv_file, delimiter=',')
       line_count = 0
       for row in csv_reader:
          if line_count > 0:
             ac.add_suggestions(Suggestion(row[1].replace('"', ''),  1.0))
             client.redis.hset(
                     "fortune500:%s" %(row[1].replace(" ", '')),
                     mapping = {
                         'title': row[1],
                         'company': row[1],
                         'rank': row[0],
                         'website': row[2],
                         'employees': row[3],
                         'sector': row[4],
                         'tags': ",".join(row[4].replace('&', '').replace(',', '').replace('  ', ' ').split()).lower(),
                         'industry': row[5],
                         'hqcity': row[8],
                         'hqstate': row[9],
                         'ceo': row[12],
                         'ceoTitle': row[13],
                         'ticker': row[15],
                         'revenues': row[17],
                         'profits': row[19],
                         'assets': row[21],
                         'equity': row[22]

                })
          line_count += 1

@app.route('/')
def index():
   if ac.len() < 1:
       load_data()
   return render_template('search.html')

@app.route('/display', methods = ['POST'])
def display():
   display = request.form
   info = search_data(display['account'])
   return render_template('results.html', result = info)

@app.route('/aggregate')
def show_agg():
   return render_template("aggregate.html")

@app.route('/showagg', methods = ['POST'])
def agg_show():
   a = request.form.to_dict()
   rows = agg_by(a['agg'])
   # Filter and Capitalize the strings
   rows=[(lambda x: [string.capwords(x[1]), x[3]])(x) for x in rows]
   return render_template('aggresults.html', rows = rows, field = a['agg'].replace("@", '').capitalize())

@app.route('/autocomplete')
def auto_complete():
    name = request.args.get('term')
    suggest = ac.get_suggestions(name, fuzzy = True)
    return(json.dumps([{'value': item.string, 'label': item.string, 'id': item.string, 'score': item.score} for item in suggest]))

@app.route('/searchceo')
def search_ceo():
   return render_template("searchceo.html")

@app.route('/displayceo', methods=['POST'])
def display_ceo():
   form = request.form.to_dict()
   ceos = [(lambda x: [x.company, x.ceo, x.ceoTitle]) (x) for x in client.search(Query(form["ceo"]).limit_fields('ceo')).docs]
   return render_template('displayceos.html', ceos = ceos)

@app.route('/searchtags')
def search_tags():
   tags = client.tagvals("tags")
   return render_template("searchtags.html", tags=tags)

@app.route('/displaytags', methods=['POST'])
def display_tags():
   tags = request.form.getlist('tgs')
   q = Query("@tags:{%s}" %("|".join(tags))).sort_by('rank', asc=True).paging(0, 100)
   res = [(lambda x: [x.rank, x.company, x.tags]) (x) for x in client.search(q).docs]
   return render_template('displaytags.html', companies = res)



if __name__ == '__main__':
   bootstrap.init_app(app)
   nav.init_app(app)
   app.debug = True
   app.run(port=5000, host="0.0.0.0")
