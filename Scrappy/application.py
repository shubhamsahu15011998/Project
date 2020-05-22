from flask import Flask, render_template,url_for, request, redirect
from flask_cors import CORS,cross_origin
import requests
#from flask_sqlalchemy import SQLAlchemy
#from datetime import datetime
from bs4 import BeautifulSoup as bs
# It is used to parse html page
from urllib.request import urlopen as uReq
import pymongo

#pip install gunicorn
#pip freeze > requirements.txt

app = Flask(__name__)

@app.route('/',methods=['GET'])
@cross_origin()
def home():
    return render_template('index.html')

@app.route('/review',methods=['POST'])
@cross_origin()
def review():
    searchString = request.form['content'].replace(" ","")
    try:
        dbConn = pymongo.MongoClient("mongodb://localhost:27017/")  # opening a connection to Mongo
        db = dbConn['crawlerDB']
        reviews = db[searchString].find({})
        if reviews.count() > 0:
            return render_template('results.html', reviews=reviews)
        else:
            flipkart_url = "https://www.flipkart.com/search?q=" + searchString
            uClient = uReq(flipkart_url)
            flipkartPage = uClient.read()
            uClient.close()
            flipkart_html = bs(flipkartPage, "html.parser")
            bigboxes = flipkart_html.findAll("div", {"class": "bhgxx2 col-12-12"})
            del bigboxes[0:3]  # Remove first three uneccesary boxes that do not contain any useful data
            box = bigboxes[0]
            productLink = "https://www.flipkart.com" + box.div.div.div.a['href']
            prodRes = requests.get(productLink,timeout=100)
            prod_html = bs(prodRes.text, "html.parser")
            commentboxes = prod_html.find_all('div', {'class': "_3nrCtb"})
            table = db[searchString]
            reviews = []
            for commentbox in commentboxes:
                try:
                    name = commentbox.div.div.find_all('p', {'class': '_3LYOAd _3sxSiS'})[0].text
                except:
                    name = 'No Name'
                try:
                    rating = commentbox.div.div.div.div.text

                except:
                    rating = 'No Rating'

                try:
                    commentHead = commentbox.div.div.div.p.text
                except:
                    commentHead = 'No Comment Heading'
                try:
                    comtag = commentbox.div.div.find_all('div', {'class': ''})
                    custComment = comtag[0].div.text
                except:
                    custComment = 'No Customer Comment'
                mydict = {"Product": searchString, "Name": name, "Rating": rating, "CommentHead": commentHead,"Comment": custComment}
                x = table.insert_one(mydict)
                reviews.append(mydict)
                return render_template('results.html', reviews=reviews)
        # return render_template('results.html')
            else:
                return render_template('index.html')
    except:
        return "An error occured"

if __name__ ==  "__main__" :
    app.run(debug=True,port=5500)