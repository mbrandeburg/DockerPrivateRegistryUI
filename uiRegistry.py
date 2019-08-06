## Set up registry
# NOTE: adapted from: https://docs.docker.com/registry/deploying/
# start up: docker run -d -p 5000:5000 --restart=always --name registry registry:2

## Add image
# Pull and tag: docker pull ubuntu:16.04 && docker tag ubuntu:16.04 localhost:5000/my-ubuntu
# Push to registry: docker push localhost:5000/my-ubuntu

## Query for image
# CLI example: curl -v -X GET http://localhost:5000/v2/_catalog

## Convert query to UI display of repos (FLASK)
import os
import requests
import pandas as pd
from pprint import pprint
from datetime import datetime
import json
import plotly
import plotly.plotly as py
import plotly.graph_objs as go
from flask import Flask, render_template, request, send_from_directory
from flask_bootstrap import Bootstrap
app = Flask(__name__)
Bootstrap(app)

# url = "http://localhost:5000/v2/_catalog"
url = "http://10.107.128.1:80/v2/_catalog" #NOTE: needs http:// (and to be on VPN)

def getCatalog(uri):
    r = requests.get(url=uri) #200 response OK
    data = r.json()
    return data['repositories'] #collect repositories - see repo variable below

### Now try with project mirror:
repos = getCatalog(url)
reposDF = pd.DataFrame(repos, columns=['Repositories'])
reposDF.index = reposDF.index+1 #offset counting by 1 for table

## JUST ADD THE TAGS TO THE DF
def tagCollector(passedRepo):
    passedRepo['Tags'] = 0
    passedRepo['Last Modified'] = 0
    for i, repository in enumerate(passedRepo['Repositories']):
        urlBase = url[:-8]
        urlTag = urlBase + "{}/tags/list".format(repository)
        r = requests.get(url=urlTag)
        data = r.json()
        repoTags = data['tags']
        passedRepo['Tags'].iloc[i] = repoTags
        # Now let's pull out last modified (repoTags[-1])
        urlTimeBase = urlBase + "{}/manifests/{}".format(repository,repoTags[-1])
        rTime = requests.get(url=urlTimeBase)
        timeData = rTime.json()
        # pprint(timeData['history'][0]['v1Compatibility']) #but problem as I need to convert string back into dict, it won't let me use number indexers
        stringStore = timeData['history'][0]['v1Compatibility']
        dictStore = json.loads(stringStore)
        # print(dictStore['created'])
        passedRepo['Last Modified'].iloc[i] = dictStore['created']

tagCollector(reposDF)
reposDF['Last Modified'] = pd.to_datetime(reposDF['Last Modified'])
# More datetime conversions b/c can't get rid of miliseconds in iso date pulled in above:
reposDF['Last Modified Date'] = reposDF['Last Modified'].dt.date 
reposDF['Last Modified Time'] = reposDF['Last Modified'].dt.time
for i in range(1, len(reposDF)+1): 
    reposDF['Last Modified Time'].loc[i] = reposDF['Last Modified Time'].loc[i].strftime('%H:%M:%S')
    reposDF['Last Modified'].loc[i] = str(reposDF['Last Modified Date'].loc[i])+" "+reposDF['Last Modified Time'].loc[i]
reposDF = reposDF.drop(columns=['Last Modified Time'])
# Now build df for graph later
valueCounts = reposDF["Last Modified Date"].value_counts().to_frame()
valueCounts = valueCounts.reset_index()
valueCounts = valueCounts.rename(columns={"Last Modified Date": "Count", "index": "Last Modified Date"})
# print(valueCounts)

# now get rid of that date only column since we have a new df for plotly
reposDF = reposDF.drop(columns=['Last Modified Date'])

## FLASK RENDER THE WEBPAGE:
# main webpage
@app.route("/")
def homePage():
    # make plotly graph dictionary for json
    trace = go.Bar(
        x = valueCounts['Last Modified Date'],
        y = valueCounts['Count'],
    )
    # now get it ready for json
    dataGraph = [trace]
    graphJSON = json.dumps(dataGraph, cls=plotly.utils.PlotlyJSONEncoder)
    return render_template('index.html', table=reposDF.to_html(), title1=url, graphJSON=graphJSON)

# favicon
@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                          'favicon.ico',mimetype='image/vnd.microsoft.icon')

### INITAITE IT VIA FLASK
if __name__ == "__main__":
    app.run(host='0.0.0.0', port=8000) #5000 is currently used by registry I believe
    # gunicorn -w 4 -b 0.0.0.0:8000 stopApp:app --timeout 500





##### SAVED FOR MAKING SEPARATE WEBPAGES FOR TAGS #####
# ## Collect tag information for subpages
# tagDF = []
# def tagCollector(passedRepo):
#     for i, repository in enumerate(passedRepo['Repositories']):
#         lister = [] # use to build DF - overwrite each loop
#         lister.append(repository)
#         tagDF.append(i) #instantiate, then overwrite [i]-th as a DF
#         tagDF[i] = pd.DataFrame(lister, columns=['Repository'])
#         tagDF[i].index = tagDF[i].index+1
# tagCollector(reposDF)
# tagCollector(reposDF2)

## Stylers to connect to sub pages on index page
# def href_maker(val):
#     return '<a href="/{}">{}</a>'.format(val,val)
# reposDF = reposDF.style.format(href_maker, subset=pd.IndexSlice[:, ['Repositories']])
# reposDF2 = reposDF2.style.format(href_maker, subset=pd.IndexSlice[:, ['Repositories']])

# @app.route("/<id>")
# def tagPage(id):
#     for i, _ in enumerate(tagDF): 
#         if tagDF[i]['Repository'].loc[[1][0]] == id:
#             displayDF = tagDF[i]
#             return render_template('tag.html', title1=id, table=displayDF.to_html())
