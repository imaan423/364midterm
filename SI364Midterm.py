###############################
####### SETUP (OVERALL) #######
###############################

## Imaan Munir

## Import statements
import os
from flask import Flask, render_template, session, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField # Note that you may need to import more here! Check out examples that do what you want to figure out what.
from wtforms.validators import Required # Here, too
from flask_sqlalchemy import SQLAlchemy
from flask_script import Manager, Shell
import requests
import json


## App setup code
app = Flask(__name__)
app.debug = True

## All app.config values
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get('DATABASE_URL') or "postgresql://localhost/imunir364midterm"
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'hard to guess string from si364'
app.config['HEROKU_ON'] = os.environ.get('HEROKU')


## Statements for db setup (and manager setup if using Manager)
db = SQLAlchemy(app)
manager = Manager(app)


######################################
######## HELPER FXNS (If any) ########
######################################


##################
##### MODELS #####
##################

class Name(db.Model):
    __tablename__ = "Name"
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(64))

    def __repr__(self):
        return "{} (ID: {})".format(self.name, self.id)


class Recipe(db.Model):
    __tablename__ = "Recipe"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(400), nullable=False)
    text = db.Column(db.String(400), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey("Name.id"), nullable=False)



###################
###### FORMS ######
###################

class SearchForm(FlaskForm):
    query = StringField("Search: ", validators=[Required()])
    submit = SubmitField()

    def validate_search(form, field):
        if len(field.data) < 1:
            raise ValidationError("Search query must be longer than zero character! Please try again!")

class NameForm(FlaskForm):
    name = StringField("Please enter your name: ", validators=[Required()])
    submit = SubmitField()

    def validate_name(form, field):
        if len(field.data) < 1:
            raise ValidationError("Name must be longer than zero character! Please try again!")
            

class InputRecipeForm(FlaskForm):
    name = StringField("Please enter your name: ", validators=[Required()])
    title = StringField("Enter recipe title: " , validators=[Required()])
    recipe = StringField("Enter list of ingredients (seperated by commas): " , validators=[Required()], render_kw={"placeholder": "e.g. 1/4 cup butter, 1/3..."})
    submit = SubmitField()

    def validate_name(form, field):
        if len(field.data) < 1:
            raise ValidationError("Name must be longer than zero character! Please try again!")
            

    def validate_title(form, field):
        if len(field.data) < 1:
            raise ValidationError("Title must be longer than zero characters! Please try again!")


    def validate_recipe(form, field):
        if len(field.data) < 1:
            raise ValidationError("Recipe must be longer than zero characters! Please try again!")


class SeeRecipeForm(FlaskForm):
    see = StringField("What recipe would you like to search?", validators=[Required()])
    submit = SubmitField() 



#######################
###### VIEW FXNS ######
#######################

@app.route('/', methods=['GET','POST'])
def home():
    form = NameForm() 
    form2 = InputRecipeForm() 
    if form2.validate_on_submit():
        title_in = form2.title.data
        name_in = form2.name.data
        recipe_in = form2.recipe.data
        if not db.session.query(Name).filter(Name.name==name_in).count():
            db.session.add(Name(name=name_in))
            db.session.commit()
        id_in = db.session.query(Name).filter(Name.name==name_in).first().id
        newrecipe = Recipe(user_id=id_in, title=title_in, text=recipe_in)
        db.session.add(newrecipe)
        db.session.commit()
        return redirect(url_for('all_recipes'))
    if form.validate_on_submit():
        name_in = form.name.data
        newname = Name()
        newname.name = name_in
        db.session.add(newname)
        db.session.commit()
        return redirect(url_for('all_names'))
    return render_template('base.html',form=form, form2=form2)
 

@app.route('/allnames')
def all_names():
    names = Name.query.all()
    allnames = []
    for item in names:
        name = item.name
        allnames.append(name)
    return render_template('all_names.html',names=allnames)


@app.route('/allrecipes')
def all_recipes():
    allrecipes = []
    see_recipe = Recipe.query.all()
    for item in see_recipe:
        entry = {}
        userid = item.user_id
        entry['recipe'] = item.text
        entry['name_of_dish'] = item.title
        entry['username'] = Name.query.filter_by(id=userid).first().name
        allrecipes.append(entry) 
    return render_template('all_recipes.html', allrecipes=allrecipes)


@app.route('/search', methods=['GET', 'POST'])
def searcher():
    id = '03b1ab77'
    key = 'e0b0bc1687f13edb721f93655b9151b9'
    form = SearchForm()
    final = []
    searched = []
    context = []
    if form.validate_on_submit():
        searched = ['searched']
        query = form.query.data
        results = db.session.query(Recipe).filter(Recipe.title==query)
        for result in results:
            entry = {}
            entry['recipe'] = result.text
            entry['name_of_dish'] = result.title
            userid = result.user_id
            entry['username'] = Name.query.filter_by(id=userid).first().name
            final.append(entry)
        if not results.count():
            q = 'https://api.edamam.com/search?q={}&app_id={}&app_key={}'.format(query,id,key)
            r = requests.get(q)
            all_results = json.loads(r.text)
            base_url = "https://www.edamam.com/"
            for item in all_results['hits']:
                current = {}
                current['label'] = item['recipe']['label']
                current['ingredients'] = item['recipe']['ingredients']
                current['url'] = '{}{}'.format(base_url ,item['recipe']['uri'].split('#')[1].replace('_','/'))
                context.append(current)
            
    return render_template('search.html', form=form, results=final, searched=searched, context=context)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404




if __name__ == '__main__':
    db.create_all() 
    manager.run() 
    app.run(use_reloader=True,debug=True) 

