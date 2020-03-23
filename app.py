from flask import Flask, render_template, request, redirect
from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import Navbar, View
from redisearch import AutoCompleter, Suggestion, Client, Query, TextField, NumericField, aggregation, reducers

import json
import redis
import csv

app = Flask(__name__)
bootstrap = Bootstrap()


nav = Nav()
topbar = Navbar('',
    View('Home', 'index'),
    View('Aggregations', 'show_agg'),
)
nav.register_element('top', topbar)

def agg_by(field):
   client = Client('fortune500')
   ar = aggregation.AggregateRequest().group_by(field, reducers.count().alias('my_count')).sort_by(aggregation.Desc('@my_count'))
   return (client.aggregate(ar).rows)

def search_data(company):
   client = Client('fortune500')
   j = client.search(Query(company).limit_fields('title').verbatim()).docs[0].__dict__
   del j['id']
   del j['payload']
   return(j)

def load_data():
   ac = AutoCompleter('ac')
   client = Client('fortune500')
   client.create_index([
      TextField('title', weight=5.0),
      TextField('website'),
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
      TextField('ticker'),
   ])
   with open('./fortune500.csv') as csv_file:
      csv_reader = csv.reader(csv_file, delimiter=',')
      line_count = 0
      for row in csv_reader:
         if line_count > 0:
            ac.add_suggestions(Suggestion(row[1].replace('"', ''),  1.0))
            client.add_document(
               row[1].replace(" ", ''),
               title = row[1],
               rank = row[0],
               website = row[2],
               employees = row[3],
               sector = row[4],
               industry = row[5],
               hqcity = row[8],
               hqstate = row[9],
               ceo = row[12],
               ceoTitle = row[13],
               ticker = row[15],
               revenues = row[17],
               profits = row[19],
               assets = row[21],
               equity = row[22]
               )
         line_count += 1

@app.route('/')
def index():
   r = redis.Redis()
   if len(r.keys('ac')) < 1:
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
   return render_template('aggresults.html', rows = rows, field = a['agg'])

@app.route('/autocomplete')
def auto_complete():
    ac = AutoCompleter('ac')
    name = request.args.get('term')
    suggest = ac.get_suggestions(name, fuzzy = True)
    return(json.dumps([{'value': item.string, 'label': item.string, 'id': item.string, 'score': item.score} for item in suggest]))


if __name__ == '__main__':
   bootstrap.init_app(app)
   nav.init_app(app)
   app.run()
