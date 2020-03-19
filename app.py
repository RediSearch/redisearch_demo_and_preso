from flask import Flask, render_template, request, redirect
from flask_bootstrap import Bootstrap
from flask_nav import Nav
from flask_nav.elements import Navbar, View
from redisearch import AutoCompleter, Suggestion, Client, Query, TextField

import json
import redis
import csv

app = Flask(__name__)
bootstrap = Bootstrap()


nav = Nav()
topbar = Navbar('',
    View('Home', 'index'),
)
nav.register_element('top', topbar)

def search_data(company):
   client = Client('fortune500')
   j = client.search(Query(company).limit_fields('title').verbatim())
   return(j.docs[0].__dict__)

def load_data():
   ac = AutoCompleter('ac')
   client = Client('fortune500')
   client.create_index([
      TextField('title', weight=5.0),
      TextField('website')
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
               website = row[2]
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
   print(info)
   return render_template('results.html', result = info)



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
