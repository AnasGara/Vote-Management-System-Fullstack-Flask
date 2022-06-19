from flask import Flask, request, Response, jsonify, make_response, render_template, flash, url_for,session, g
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import table, text
from sqlalchemy.orm import relationship, Session
from werkzeug.utils import secure_filename, redirect

from  werkzeug.security import generate_password_hash, check_password_hash
import jwt
from datetime import datetime, timedelta
from flask_mail import Mail, Message
#test __init__.py

import os
from functools import wraps

from werkzeug.wsgi import get_current_url
from datetime import datetime



app = Flask(__name__)

mail = Mail(app)  # instantiate the mail class

# configuration of mail
app.config['MAIL_SERVER']='smtp.mailtrap.io'
app.config['MAIL_PORT'] = 2525
app.config['MAIL_USERNAME'] = '742a8884d1501c'
app.config['MAIL_PASSWORD'] = '3dd05853e4f9ad'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
mail = Mail(app)
app.secret_key = os.getenv("SECRET_KEY")
app.config['UPLOAD_FOLDER'] = os.getenv("UPLOAD_FOLDER")
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("DATA_BASE_URL")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
ALLOWED_EXTENSIONS_IMG = set(['png', 'jpg', 'jpeg', 'gif'])
ALLOWED_EXTENSIONS_VID = set(['mp4','mkv'])


def allowed_file_img(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_IMG
def allowed_file_vid(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS_VID
db =SQLAlchemy(app)


# participer = db.Table('participer',
#     db.Column('user_id',db.Integer,db.ForeignKey('user.id'),primary_key=True),
#     db.Column('competition_id',db.Integer,db.ForeignKey('competition.id'),primary_key=True),
#     db.Column('video',db.String(100),nullable=True),
#     db.Column('img',db.String(100),nullable=True)
# )
@app.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

class Participer(db.Model):
    __tablename__ = 'participer'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    competition_id = db.Column(db.Integer, db.ForeignKey('competition.id'), primary_key=True)
    video = db.Column(db.String(100),nullable=True)
    img = db.Column(db.String(100),nullable=False)
    desc = db.Column(db.String(500), nullable=True)
    user = db.relationship("User", back_populates="part_comp")
    competition = db.relationship("Competition", back_populates="participants")



# voter = db.Table('voter',
#     db.Column('user_id',db.Integer,db.ForeignKey('user.id'),primary_key=True),
#     db.Column('competition_id',db.Integer,db.ForeignKey('competition.id'),primary_key=True),
#     db.Column('user_benf',db.Integer,db.ForeignKey('user.id')),
# )

class voter(db.Model):
    __tablename__ = 'voter'
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'),primary_key=True)
    competition_id = db.Column(db.Integer, db.ForeignKey('competition.id'),primary_key=True)
    user_benf = db.Column(db.Integer(),db.ForeignKey('user.id'))
    userv = db.relationship("User",  foreign_keys=[user_id],backref="part_vot")
    userb = db.relationship("User", foreign_keys=[user_benf], backref="voted")
    competition = db.relationship("Competition",back_populates="voters")


class Competition(db.Model):
    __tablename__ = 'competition'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(100), nullable=False)
    limit_date = db.Column(db.String(100), nullable=False)
    desc = db.Column(db.String(500), nullable=False)
    media = db.Column(db.String(100), nullable=True)
    valid = db.Column(db.Integer, default=0, nullable=True)
    closed = db.Column(db.Integer, default=0, nullable=True)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'),nullable=False)



    participants = db.relationship('Participer', back_populates="competition",cascade="all,delete")
    voters = db.relationship('voter', back_populates="competition",cascade="all,delete")

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key = True,unique = True)
    first_name = db.Column(db.String(100),nullable=False)
    last_name = db.Column(db.String(100),nullable=False)
    # birth_date = db.Column(db.Date,nullable=True)
    phone = db.Column(db.String(50),nullable=False)
    email = db.Column(db.String(70), unique = True,nullable=False)
    password = db.Column(db.String(80),nullable=False)
    admin = db.Column(db.Integer,default=0,nullable=False)

    created_comp = db.relationship('Competition',backref='userCompetitions',lazy=True)
    part_comp = db.relationship('Participer', back_populates="user")










db.create_all()
@app.route('/',methods=['GET'])
def home():
    page = request.args.get('page', 1, type=int)
    comp_list = Competition.query.filter_by(valid = 1).paginate(page=page,per_page=3)
    return render_template('index.html',comp_list=comp_list)
#image upload
# @app.route('/tt')
# def home():
#     return render_template('upload.html')
# @app.route('/tt', methods=['POST'])
# def upload_image():
#     if 'file' not in request.files:
#         flash('No file part')
#         return redirect(request.url)
#     file = request.files['file']
#     if file.filename == '':
#             flash('No image selected for uploading')
#             return redirect(request.url)
#     if file and allowed_file(file.filename):
#         filename = secure_filename(file.filename)
#         filename = "hello"+filename
#         file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
#         # print('upload_image filename: ' + filename)
#         flash('Image successfully uploaded and displayed below')
#         return render_template('upload.html', filename=filename)
#     else:
#         flash('Allowed image types are - png, jpg, jpeg, gif')
#         return redirect(request.url)
#
# @app.route('/display/<filename>')
# def display_image(filename):
#     #print('display_image filename: ' + filename)
#     return redirect(url_for('static', filename='uploads/' + filename), code=301)
@app.route("/vote" ,methods=['POST'])
def vote():
    data = request.form
    comp = data['comp_id']
    user_voter = g.user.id
    user_benf = data['user_benf']
    vote = voter(user_id=user_voter, competition_id=comp, user_benf=user_benf)
    db.session.add(vote)
    db.session.commit()
    return redirect(url_for("detail_competition", comp_id=comp))


@app.route("/delete_comp/<int:comp_id>/<string:route>")
def delete_comp(comp_id,route):
    comp = Competition.query.filter_by(id=comp_id).first()
    db.session.delete(comp)
    db.session.commit()
    flash("Competition "+str(comp.title)+"e has been Deleted")
    if(route == 'valid_comp' or route == 'comps'):
        msg = Message(
            'Vote.ly status',
            sender='Votely <contact@vote.ly>',
            recipients=[comp.userCompetitions.email]
        )
        msg.html = render_template('noEmail.html',comp=comp)
        mail.send(msg)
        return redirect(url_for(route))
    return redirect(url_for(route))

@app.route('/mycomp',methods=['GET'])
def user_comp():
    if not g.user:
        return redirect(url_for('login'))
    res = User.query.get(g.user.id).created_comp
    return render_template('user_competitions.html',res=res)
@app.route('/create_part',methods=['POST','GET'])
def create_participation():

    data = request.form
    comp = data['comp']
    file = request.files['media']

    if file and allowed_file_vid(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER']+"/vid/", filename))
    else:
        flash('Allowed video type is mp4','error')
        success = False
        return redirect(url_for("detail_competition",comp_id=comp,success=success))


    id = g.user.id
    part = Participer(user_id=id,competition_id=comp,video=filename,desc=data['desc'])
    db.session.add(part)
    db.session.commit()
    flash('Your participation has been added')
    success = True
    return redirect(url_for("detail_competition",comp_id=comp,success=success))

@app.route('/competition')
def create_competition():
    if not g.user:
        return redirect(url_for('login'))
    return render_template('create_comp.html')
@app.route('/competition/<int:comp_id>')
def detail_competition(comp_id):
    comp = Competition.query.get(comp_id)
    # result = db.session.execute('select * from participer where competition_id = :comp_id ', {'comp_id': comp_id})
    # part_datas =result
    partcip = True
    vot = True
    if(not g.user):
        return render_template('comp_details.html', comp=comp, partcip=partcip)
    result = db.session.execute('select * from Participer where competition_id = :comp_id and user_id= :id', {'comp_id': comp_id,'id':g.user.id})
    if([row[0] for row in result] ):
        partcip = False
    res = db.session.execute('select * from voter where competition_id = :comp_id and user_id= :id',
                                {'comp_id': comp_id, 'id': g.user.id})
    if ([row[0] for row in res]):
        vot = False
    win = db.session.execute('select count(user_benf) as rs,user_benf from voter where competition_id = :comp_id group by user_benf order by rs desc', {'comp_id': comp_id})
    winners =[row[1] for row in win]
    gold=0
    silver=0
    bronze=0
    silvervid=0
    goldvid=0
    bronzevid=0
    if(comp.closed == 1):
        gold = User.query.get(winners[0])
        silver = User.query.get(winners[1])
        bronze = User.query.get(winners[2])
        for elem in range(len(silver.part_comp)):
            if silver.part_comp[elem].competition_id == comp_id:
                silvervid=elem
        for elemg in range(len(gold.part_comp)):
            if gold.part_comp[elemg].competition_id == comp_id:
                goldvid=elemg
        for elemb in range(len(bronze.part_comp)):
            if bronze.part_comp[elemb].competition_id == comp_id:
                bronzevid=elemb
    return render_template('comp_details.html',comp=comp,partcip=partcip,vot=vot,gold=gold,silver=silver,bronze=bronze,goldvid=goldvid,silvervid=silvervid,bronzevid=bronzevid)
@app.route('/user',methods=['POST'])
def create_user():
    data = request.json

    first_name = data['first_name']
    last_name = data['last_name']
    email = data['email']
    phone = data['phone']
    password = data['password']

    newUser = User(first_name = first_name,last_name=last_name,phone=phone,email=email,password=password)
    db.session.add(newUser)
    db.session.commit()
    return jsonify({"success": True, "response": "User added", "status":201})

@app.route("/create_comp", methods=["POST"])
def add():
    data = request.form
    title = data['title']
    type = data['type']
    limit_date = data['limit_date']
    desc = data['desc']
    if 'media' not in request.files:
        flash('No file part')
        return redirect(url_for("create_competition"))
    file = request.files['media']
    if file.filename == '':
        flash('No image selected for uploading')
        return redirect(url_for("create_competition"))
    if file and allowed_file_img(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER']+"/img/", filename))
        #print('upload_image filename: ' + filename)
    else:
        flash('Allowed image types are - png, jpg, jpeg')
        return redirect(url_for("create_competition"))

    newComp = Competition()

    newComp.title = title
    newComp.type = type
    newComp.limit_date = limit_date
    newComp.desc = desc
    newComp.media = filename
    newComp.creator_id = g.user.id
    db.session.add(newComp)
    db.session.commit()
    flash('Competition created successfully')
    return redirect(url_for("create_competition"))

# @app.route('/competition',methods=['POST'])
# def create_comp():
#     data = request.json
#
#     title = data['title']
#     type = data['type']
#     limit_date = data['limit_date']
#     desc = data['desc']
#     media = data['media']
#     creator_id = data['creator_id']
#
#     newComp = Competition()
#     newComp.title = title
#     newComp.type = type
#     newComp.limit_date = limit_date
#     newComp.desc = desc
#     newComp.media = media
#     newComp.creator_id = creator_id
#
#     db.session.add(newComp)
#     db.session.commit()
#     return jsonify({"success": True, "response": "Competition added", "status":201})


@app.before_request
def before_request():
    g.user = None

    if 'user_id' in session:
        user = User.query.filter_by(id=session['user_id']).first()
        g.user = user



@app.route('/login', methods=['GET', 'POST'])
def login():  # put application's code here

    if not g.user:
        if request.method == 'POST':
            session.pop('user_id', None)

            email = request.form['email']
            password = request.form['password']

            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password, password):
                session['user_id'] = user.id
                return redirect(url_for('home'))
            flash('email or password is wrong')
            return render_template('login.html')

        return render_template('login.html')
    return redirect(url_for('home'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if not g.user:
        if request.method == 'POST':
            session.pop('user_id', None)
            fname = request.form['first_name']
            lname = request.form['last_name']
            email = request.form['email']
            pwd = request.form['password']
            phone = request.form['phone']

            user = User(first_name=fname,last_name=lname,phone=phone,email=email,password=generate_password_hash(pwd))
            db.session.add(user)
            db.session.commit()
            session['user_id'] = user.id
            return redirect(url_for('home'))

        return render_template('signup.html')
    return redirect(url_for('home'))




#admin routes

@app.route('/login_admin', methods=['GET', 'POST'])
def login_admin():  # put application's code here

    if not g.user:
        if request.method == 'POST':
            session.pop('user_id', None)

            email = request.form['email']
            password = request.form['password']

            user = User.query.filter_by(email=email).first()
            if user and check_password_hash(user.password, password) and user.admin == 1:
                session['user_id'] = user.id
                return redirect(url_for('admin_home'))
            flash('email or password is wrong')
            return render_template('admin_login.html')

        return render_template('admin_login.html')
    return redirect(url_for('admin_home'))


@app.route('/admin')
def admin_home():
    if not g.user:
        return redirect(url_for('login_admin'))
    count_comps = Competition.query.count()
    count_users = User.query.count()
    return render_template('admin_home.html',count_comps=count_comps,count_users=count_users)

@app.route('/valid_comp')
def valid_comp():
    if not g.user:
        return redirect(url_for('login_admin'))
    invalid_comp = Competition.query.filter_by(valid = 0).all()
    return render_template('valid_comp.html',invalid_comp=invalid_comp)

@app.route('/compdetail/<int:comp_id>')
def admin_comp_detail(comp_id):
    if not g.user:
        return redirect(url_for('login_admin'))
    comp = Competition.query.get(comp_id)
    return render_template('admin_comp_detail.html',comp=comp)

@app.route('/validate/<int:comp_id>')
def validate(comp_id):
    if not g.user:
        return redirect(url_for('login_admin'))
    comp = Competition.query.get(comp_id)
    comp.valid = 1
    db.session.commit()
    msg = Message(
        'Vote.ly status',
        sender='Votely <contact@vote.ly>',
        recipients=[comp.userCompetitions.email]
    )
    msg.html = render_template('okEmail.html',comp=comp)
    mail.send(msg)
    flash("Competition "+str(comp.title)+" has been validated")
    return redirect(url_for("valid_comp"))

@app.route('/users')
def users():
    if not g.user:
        return redirect(url_for('login_admin'))
    users = User.query.all()
    return render_template('admin_users.html',users=users)

@app.route("/delete_user/<int:user_id>")
def delete_user(user_id):
    user = User.query.get(user_id)
    db.session.delete(user)
    db.session.commit()

    flash("User "+str(user.first_name)+" has been Deleted")
    return redirect(url_for("users"))


@app.route('/admin_competitions')
def comps():
    if not g.user:
        return redirect(url_for('login_admin'))
    comps = Competition.query.all()
    return render_template('admin_competitions.html',comps=comps)



@app.route('/close/<int:comp_id>')
def close(comp_id):
    if not g.user:
        return redirect(url_for('user_comp'))
    comp = Competition.query.get(comp_id)
    comp.closed = 1
    db.session.commit()
    flash("Competition "+str(comp.title)+" is now closed")
    return redirect(url_for("user_comp"))

@app.route('/logout/<string:route>')
def sign_out(route):
    session.pop('user_id')
    log_out = False
    return redirect(url_for(route,log_out=log_out))

if __name__ == '__main__':
    app.run()
