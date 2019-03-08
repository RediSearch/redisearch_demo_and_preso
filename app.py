from flask import Flask, render_template, request, redirect
from redisearch import AutoCompleter, Suggestion
import json
import csv

app = Flask(__name__)

@app.route('/')
def hello_world():
   return render_template('search.html')

@app.route('/autocomplete')
def auto_complete():
    ac = AutoCompleter('ac')
    name = request.args.get('term')
    suggest = ac.get_suggestions(name, fuzzy = True)
    return(json.dumps([{'value': item.string, 'label': item.string, 'id': item.string, 'score': item.score} for item in suggest]))

@app.route('/loaddata')
def load_data():
   ac = AutoCompleter('ac')
   with open('./fortune500.csv') as csv_file:
      csv_reader = csv.reader(csv_file, delimiter=',')
      line_count = 0
      for row in csv_reader:
         if line_count > 0:
            ac.add_suggestions(Suggestion(row[1].replace('"', ''),  1.0))
         line_count += 1
   return redirect("/", code=302)


if __name__ == '__main__':
   app.run()
