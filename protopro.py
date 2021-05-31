from flask import Flask, render_template, flash, redirect, session, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, date
from flask_wtf import FlaskForm
from wtforms.ext.sqlalchemy.orm import model_form
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, PasswordField, validators

app = Flask(__name__)
app.secret_key = "ohpiH5ahy7ohg%u4ieb%aep5aehaos"
app.config["SQLALCHEMY_DATABASE_URI"] = 'postgresql:///anders'
db = SQLAlchemy(app)

class Game(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  title = db.Column(db.String, nullable=False)
  platform = db.Column(db.String, nullable=False)
  onsale = db.Column(db.Boolean, nullable=True, default=True)
  price = db.Column(db.Float, nullable=False)
  discount = db.Column(db.Integer, nullable=True)
  bywhom = db.Column(db.String, nullable=False)
  sale_ends_in_UTC = db.Column(db.Date, nullable=True)
  added_autofilled =  db.Column(db.DateTime, nullable=True, default=datetime.utcnow)
  comment = db.Column(db.Text, nullable=True)

GameForm = model_form(Game, base_class=FlaskForm, exclude=["added_autofilled"], db_session=db.session)

app.before_first_request
def initDb():
  db.create_all()

#  game = Game(title="Lost Planet 2", platform="Xbox 360", price="4.95", discount="75", bywhom="Jay", comment="Seems like a good 4-player title, should we grab it?")
#  db.session.add(game)

# game = Game(title="Among US", platform="PC", price="3.95", bywhom="Ben", comment="It's a new release, would you guys be willing to play it with me?")
# db.session.add(game)

# db.session.commit()

class User(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  email = db.Column(db.String, nullable=False, unique=True)
  passwordHash = db.Column(db.String, nullable=False)

  def setPassword(self, password):
    self.passwordHash = generate_password_hash(password)

  def checkPassword(self, password):
    return check_password_hash(self.passwordHash, password)

class UserForm(FlaskForm):
  email = StringField("email", validators=[validators.Email()])
  password = PasswordField("password", validators=[validators.InputRequired()])

class RegisterForm(UserForm):
  key = StringField("registration key", validators=[validators.InputRequired()])

@app.errorhandler(403)
def custom403(e):
  return redirect("/user/login")

@app.errorhandler(404)
def custom404(e):
  return render_template("404.html")

def currentUser():
  try:
    uid = int(session["uid"])
  except:
    return None
  return User.query.get(uid)

app.jinja_env.globals["currentUser"] = currentUser

def loginRequired():
  if not currentUser():
    abort(403)

#user
@app.route("/user/login", methods =["GET", "POST"])
def loginView():
  form = UserForm()

  if  form.validate_on_submit():
      email = form.email.data
      password = form.password.data

      user = User.query.filter_by(email=email).first()
      if not user:
        flash("Login failed. Please create an account if you haven't done so yet.")
        return redirect("/user/login")
      if not user.checkPassword(password):
        flash("Login failed")
        return redirect("/user/login")

      session ["uid"] = user.id
      flash("Welcome!")
      return redirect("/")

  return render_template("login.html", form=form)

@app.route("/user/register", methods=["GET", "POST"])
def registerView():
  form = RegisterForm()

  if  form.validate_on_submit():
      email = form.email.data
      password = form.password.data

      if User.query.filter_by(email=email).first():
        flash("User alreday exists - please log in!")
        return redirect("/user/login")

      if form.key.data !="excelsior":
        flash("Sorry, wrong key")
        return redirect("/user/register")

      user = User(email=email)
      user.setPassword(password)

      db.session.add(user)
      db.session.commit()
      flash("Register")
      return redirect("/user/login")

  return render_template("register.html", form=form)


@app.route("/user/logout")
def logoutView():
  session["uid"] = None
  flash("Bye until next time!")
  return redirect("/")

@app.before_first_request
def initDb():
  db.create_all()

#game
@app.route("/game/<int:id>/edit", methods=["GET", "POST"])
@app.route ("/game/add", methods=["GET", "POST"])
def addView(id=None):
  loginRequired()
  game = Game()
  if id:
    game = Game.query.get_or_404(id)

  form = GameForm(obj=game)

  if form.validate_on_submit():
    form.populate_obj(game)
    db.session.add(game)
    db.session.commit()

    flash("Your entry has been recorded!")
    return redirect("/")

  return render_template("add.html", form=form)

@app.route("/game/<int:id>/delete")
def deleteView(id):
  loginRequired()
  game = Game.query.get_or_404(id)
  db.session.delete(game)
  db.session.commit()

  flash("Deleted")
  return redirect("/")

@app.route("/")
def indexView():
  games = Game.query.order_by(Game.added_autofilled.desc())  #Game.title
  #games = Game.query.all()
  return render_template("index.html", games=games)

if __name__=="__main__":
  app.run(debug=True)
