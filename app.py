from flask import Flask, render_template, request, session, redirect
from flask_sqlalchemy import SQLAlchemy
from base64 import b64decode
import json
import os
import math
from datetime import datetime


with open('config.json', 'r') as file_:
    params = json.load(file_)["params"]

app = Flask(__name__)
app.secret_key = 'my-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = params['remote_uri']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Volunteers(db.Model):
    SerialNumber = db.Column(db.Integer, primary_key=True)
    EventNumber = db.Column(db.Integer, nullable=False)
    Age = db.Column(db.Integer, nullable=False)
    Name = db.Column(db.String(120), nullable=False)
    Event = db.Column(db.String(120), nullable=False)
    Duty = db.Column(db.String(120), nullable=False)
    RegistrationDate = db.Column(db.String(120), nullable=False)
    PhoneNumber = db.Column(db.String(120), nullable=False)

    def __repr__(self):
        return self.id

class Events(db.Model):
    SerialNumber = db.Column(db.Integer, primary_key=True)
    EventNumber = db.Column(db.Integer, nullable=False)
    EventName = db.Column(db.String(80), nullable=False)
    EventDate = db.Column(db.String(21), nullable=False)
    Tagline = db.Column(db.String(120), nullable=False)
    Description = db.Column(db.String(120), nullable=False)
    slug = db.Column(db.String(30), nullable=False)
    img1 = db.Column(db.LargeBinary)
    img2 = db.Column(db.LargeBinary)

    def __repr__(self):
        return self.id

class Feedbacks(db.Model):
    SerialNumber = db.Column(db.Integer, primary_key=True)
    Name = db.Column(db.String(80), nullable=False)
    Email = db.Column(db.String(21), nullable=False)
    Feedback = db.Column(db.String(120), nullable=False)
    Date = db.Column(db.String(12), nullable=False)

    def __repr__(self):
        return self.id


@app.route('/')
def index():
    # return render_template('login_home.html')
    return redirect('/home')

def get_image(the_id):
    return Events.query.filter(Events.SerialNumber == the_id).first()

def get_images():
    return Events.query.all()

@app.route('/images/db/', methods=['GET'])
def get_images_from_db():
    images = get_images()
    images = list(filter(lambda img: img.img1 != None, images))
    return render_template('index.html', params=params, events=images)

@app.route('/images/db/1/<int:the_id>', methods=['GET'])
def get_image_from_db1(the_id):
    image = get_image(the_id)
    return app.response_class(image.img1, mimetype='application/octet-stream')

@app.route('/images/db/2/<int:the_id>', methods=['GET'])
def get_image_from_db2(the_id):
    image = get_image(the_id)
    return app.response_class(image.img2, mimetype='application/octet-stream')

@app.route("/home/")
def home():
    events = Events.query.filter_by().all()
    last=int(math.ceil(len(events)/int(params['no_of_events'])))
    page = request.args.get('page')
    if(not str(page).isnumeric()):
        page=1
    
    page=int(page)
    events = events[(page-1)*int(params['no_of_events']):(page-1)*int(params['no_of_events'])+int(params['no_of_events'])]
    if(page==1):
        prev="#"
        next="/home/?page="+str(page+1)
    elif(page==last):
        prev="/home/?page="+str(page-1)
        next="#"
    else:
        prev="/home/?page="+str(page-1)
        next="/home/?page="+str(page+1)
    
    events = list(filter(lambda event: event.img1 != None, events))
    return render_template('index.html', params=params, events=events, prev=prev, next=next)


@app.route("/event/<string:event_slug>", methods=['GET'])
def event_route(event_slug):
    event = Events.query.filter_by(slug=event_slug).first()
    volunteers = Volunteers.query.filter_by(EventNumber=event.EventNumber)
    return render_template('event.html', params=params, event=event, volunteers=volunteers)

@app.route("/about")
def about():
    return render_template('about.html', params=params)

@app.route("/author")
def author():
    return render_template('author.html')


@app.route("/dashboard", methods=['GET','POST'])
def dashboard():
    if('user' in session and session['user'] == params['admin_user']):
        events = Events.query.all()
        return render_template('dashboard.html', params=params, events=events)

    if request.method=='POST':
        username = request.form.get('uname')
        userpass = request.form.get('pass')
        if (username == params['admin_user'] and userpass == params['admin_password']):
            session['user']=username
            events = Events.query.all()
            return render_template('dashboard.html', params=params, events=events)

    return render_template('login.html',params=params)

@app.route("/display-feedbacks")
def display_feedbacks():
    if('user' in session and session['user'] == params['admin_user']):
        feedbacks = Feedbacks.query.all()
        return render_template('display-feedbacks.html', params=params, feedbacks=feedbacks)


import numpy as np
import pickle
import cv2
import os
import sklearn

def check_image(uploaded_file):
    selected_model = 'modelConv.pkl' #can be model.pkl
    model = pickle.load(open(selected_model,'rb'))
    image_path = os.path.join('static', uploaded_file.filename)
    uploaded_file.save(image_path)
    img = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)
    # if(selected_model=='modelConv.pkl'):
    #     img = cv2.resize(img, (64,64)).flatten()
    # else:
    img = cv2.resize(img, (128,128)).flatten()
    img = np.asarray(img)
    prediction = model.predict([img])
    messy_clean=0
    if(prediction[0]>0.5):
        messy_clean=1 # 1 means it's clean and we can't store in data base
    return messy_clean
    

@app.route("/edit/<string:sno>",methods = ['GET','POST'])
def edit(sno):
    if('user' in session and session['user'] == params['admin_user']):
        if request.method=='POST':
            EventName = request.form.get('EventName')
            Tagline = request.form.get('Tagline')
            slug = request.form.get('slug')
            Description = request.form.get('Description')
            EventNumber = request.form.get('EventNumber')
            EventDate = request.form.get('EventDate')

            File1 = request.files['file1']
            File2 = request.files['file2']

            File11 = request.files['file11']
            File22 = request.files['file22']

            check=0
            check=check_image(File11)
            check=check_image(File22)
            

            if(check==0):
                return "Sorry, The images did not pass the Dirty Image Classification test and failed to create an Event."


            if(sno=='0'):
                event = Events(EventName=EventName,EventDate=EventDate,Tagline=Tagline,Description=Description,EventNumber=EventNumber,slug=slug,img1=File1.read(),img2=File2.read())
                db.session.add(event)
                db.session.commit()
                
            else:
                event = Events.query.filter_by(SerialNumber=sno).first()
                event.EventName = EventName
                event.slug = slug
                event.Description = Description
                event.Tagline = Tagline
                event.EventNumber = EventNumber
                event.EventDate = EventDate
                event.img1 = img1
                event.img2 = img2
                db.session.commit()
                return redirect('/edit/'+sno)

            
            
        event = Events.query.filter_by(SerialNumber=sno).first()
        return render_template('edit.html',params=params, sno=sno, event=event)


@app.route("/logout")
def logout():
    session.pop('user')
    return redirect('/dashboard')

@app.route("/delete/<string:sno>",methods = ['GET','POST'])
def delete(sno):
    if('user' in session and session['user'] == params['admin_user']):
        event = Events.query.filter_by(SerialNumber=sno).first()
        db.session.delete(event)
        db.session.commit()
    return redirect('/dashboard')

@app.route("/register", methods = ['GET', 'POST'])
def register():
    events = Events.query.filter_by().all()
    if(request.method=='POST'):
        Name = request.form.get('Name')
        Age = request.form.get('Age')
        Event = request.form.get('Event')
        EventNumber = request.form.get('EventNumber')
        Duty = request.form.get('Duty')
        PhoneNumber = request.form.get('PhoneNumber')
        entry = Volunteers(Name=Name, Age = Age, Event=Event, EventNumber=EventNumber, Duty=Duty, RegistrationDate=datetime.now() , PhoneNumber=PhoneNumber)
        db.session.add(entry)
        db.session.commit()
        return render_template('/thankyou.html')
    return render_template('register.html', params=params, events=events)

@app.route("/feedback", methods = ['GET', 'POST'])
def feedback():
    if(request.method=='POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        feedback = request.form.get('feedback')
        entry = Feedbacks(Name=name, Email = email, Feedback = feedback, Date= datetime.now() )
        db.session.add(entry)
        db.session.commit()
        return render_template('/thankyou.html')
    return render_template('feedback.html', params=params)


import joblib

def convert(value):
    if(value=="Yes"):
        return 1
    else:
        return 0


@app.route("/survey", methods = ['GET', 'POST'])
def survey():
    if(request.method=='POST'):
        name = request.form.get('name')
        email = request.form.get('email')
        enough_number_of_dustbins = convert(request.form.get('enough_number_of_dustbins'))
        is_municipal_corporation_active = convert(request.form.get('is_municipal_corporation_active'))
        illness_due_to_unhygien_env = convert(request.form.get('illness_due_to_unhygien_env'))
        prev_cleanliness_campaign = convert(request.form.get('prev_cleanliness_campaign'))
        any_stray_animals_present = convert(request.form.get('any_stray_animals_present'))
        aware_about_cleanliness = convert(request.form.get('aware_about_cleanliness'))
        is_waste_in_dustbin_always = convert(request.form.get('is_waste_in_dustbin_always'))
        model = joblib.load('survey_prediction_model.pk1')
        result = model.predict([[enough_number_of_dustbins,
        is_municipal_corporation_active,
        illness_due_to_unhygien_env,
        prev_cleanliness_campaign,
        any_stray_animals_present,
        aware_about_cleanliness,
        is_waste_in_dustbin_always]])[0]
        if(result == 0):
            result = "Not Clean"
        else:
            result = "Clean"
        return render_template('/survey-result.html',args=result)
    return render_template('survey.html', params=params)


if __name__ == "__main__":
    app.run(debug=True)
