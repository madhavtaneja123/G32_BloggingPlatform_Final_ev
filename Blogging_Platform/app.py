from flask import Flask,render_template,redirect,url_for,flash,request,session,jsonify
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
import os
from flask import request, jsonify
from flask_cors import CORS

app=Flask(__name__)
CORS(app)
app.secret_key="your_secret_key"
bcrypt=Bcrypt(app)

BASE_DIR=os.path.abspath(os.path.dirname(__file__))
DB_PATH=os.path.join(BASE_DIR,"app.db")

app.config['SQLALCHEMY_DATABASE_URI']=f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False

db=SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

class User(db.Model, UserMixin):
    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(100),nullable=False,unique=True)
    email=db.Column(db.String(120),unique=True,nullable=False)
    mobileno=db.Column(db.String(15),unique=True,nullable=False)
    password_hash=db.Column(db.String(255),nullable=False)
    role=db.Column(db.String(50),nullable=False,default="user")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args,**kwargs):
        if not current_user.is_authenticated or current_user.role!="admin":
            flash("Access restricted to admins only!","danger")
            return redirect(url_for("home"))
        return f(*args,**kwargs)
    return decorated_function

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class Feedback(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    first_name=db.Column(db.String(50),nullable=False)
    last_name=db.Column(db.String(50),nullable=False)
    email=db.Column(db.String(100),nullable=True)
    rating=db.Column(db.Integer,nullable=False)
    feedback_message=db.Column(db.Text,nullable=False)

class Blog(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    title=db.Column(db.String(20),nullable=False)
    content=db.Column(db.String(1000),nullable=False)
    author_name=db.Column(db.String(100),nullable=False)
    author_email=db.Column(db.String(100),nullable=False)
    category=db.Column(db.String(100),nullable=False)
    created_at=db.Column(db.DateTime, default=db.func.current_timestamp())
    comments=db.relationship("Comment",backref="blog_comments",lazy=True,cascade="all,delete-orphan")
    likes=db.relationship("Like",backref="blog_likes",lazy=True, cascade="all,delete-orphan")
    created_by_django = db.Column(db.Boolean, default=False)

class Like(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    blog_id=db.Column(db.Integer,db.ForeignKey("blog.id"),nullable=False)
    user_ip=db.Column(db.String(100),nullable=False)

class Comment(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    blog_id=db.Column(db.Integer, db.ForeignKey("blog.id"),nullable=False)
    name=db.Column(db.String(100),nullable=False)
    email=db.Column(db.String(100),nullable=False)
    comment_text=db.Column(db.Text,nullable=False)
    created_at=db.Column(db.DateTime, default=db.func.current_timestamp())

with app.app_context():
    db.create_all() 
    if not User.query.filter_by(role="admin").first():
            admin_user = User(username="Admin", email="admin@gmail.com", mobileno="1234567890", role="admin")
            admin_user.set_password("admin123") 
            db.session.add(admin_user)
            db.session.commit()
            print("Admin user created with email: admin@gmail.com and password:admin123")


@app.route("/index")
def index():
    return render_template("index.html")

@app.route('/about')
@login_required
def about():
    images={
        'team1':'images/madhav.jpg',
        'team2':'images/manik.jpg',
        'team3':'images/divyansh.jpg',
        'team4':'images/aryan.jpg'
    }
    return render_template('about.html',images=images)

@app.route("/feedback",methods=["GET"])
@login_required
def feedback():
    return render_template("feedback_form.html")

@app.route("/submit_feedback",methods=["POST"])
def submit_feedback():
    if request.method=="POST":
        first_name=request.form.get("first_name")
        last_name=request.form.get("last_name")
        email=request.form.get("email",None)
        rating=request.form.get("rating","0")
        feedback_message=request.form.get("feedback_message")

        try:
            new_feedback=Feedback(
                first_name=first_name,
                last_name=last_name,
                email=email,
                rating=rating,
                feedback_message=feedback_message
            )
            db.session.add(new_feedback)
            db.session.commit()
            flash("Thank you for your feedback!","success")
            return redirect(url_for("our_feedbacks"))
        except Exception as e:
            db.session.rollback()
            print("Error:",e)
            flash("Error:Could not submit feedback.","danger")
            return redirect(url_for("feedback"))

@app.route("/our_feedbacks")
@login_required
def our_feedbacks():
    feedbacks=Feedback.query.all()  
    indexed_feedbacks=[(i+1,feedback)for i,feedback in enumerate(feedbacks)]
    return render_template("our_feedbacks.html",feedbacks=indexed_feedbacks)

@app.route("/create_blogs",methods=["GET","POST"])
@login_required
def create_blogs():
    if request.method=="POST":
        author_name=request.form["author_name"]
        author_email=request.form["author_email"]
        title=request.form["title"]
        category=request.form["category"]
        content=request.form["content"]
        new_blog=Blog(
            author_name=author_name,
            author_email=author_email,
            title=title,
            category=category,
            content=content)
        db.session.add(new_blog)
        db.session.commit()
        flash("Blog Published Successfully!","success")
        return redirect(url_for("display_blogs"))
    return render_template("create_blogs.html")

@app.route("/display_blogs",methods=["GET","POST"])
@login_required
def display_blogs():
    all_blogs=Blog.query.order_by(Blog.created_at.desc()).all()
    return render_template("display_blogs.html",blogs=all_blogs)


@app.route("/like_blog/<int:id>",methods=["POST"])
@login_required
def like_blog(id):
    user_ip=request.remote_addr
    existing_like=Like.query.filter_by(blog_id=id, user_ip=user_ip).first()
    if existing_like:
        db.session.delete(existing_like)
        db.session.commit()
        flash("You unliked this blog!","info")
    else:
        new_like=Like(blog_id=id,user_ip=user_ip)
        db.session.add(new_like)
        db.session.commit()
        flash("You liked this blog!","success")
    return redirect(url_for("display_blogs"))

@app.route("/delete_blog/<int:id>",methods=["GET", "POST"])
@login_required
def delete_blog(id):
    blog=Blog.query.get_or_404(id)
    if current_user.role!="admin" and blog.author_email!=current_user.email:
        flash("You can only delete your own blog!","danger")
        return redirect(url_for("display_blogs"))
    if request.method=='POST':
        db.session.delete(blog)
        db.session.commit()
        flash("Blog deleted successfully!","success")
        return redirect(url_for("display_blogs"))

@app.route('/edit_blog/<int:id>',methods=["GET", "POST"])
@login_required
def edit_blog(id):
    blog=Blog.query.get_or_404(id)
    if current_user.role!="admin" and blog.author_email!=current_user.email:
        flash("You can only edit your own blog!","danger")
        return redirect(url_for("display_blogs"))
    if request.method=='POST':
        blog.title=request.form['title']
        blog.category=request.form['category']
        blog.content=request.form['content']
        db.session.commit()
        flash("Blog updated successfully!","success")
        return redirect(url_for('display_blogs'))
    return render_template("edit_blog.html",blog=blog)

@app.route("/comment_blog/<int:id>",methods=["POST"])
@login_required
def comment_blog(id):
    name=request.form["name"]
    email=request.form["email"]
    comment_text=request.form["comment_text"]
    new_comment=Comment(blog_id=id,name=name, email=email,comment_text=comment_text)
    db.session.add(new_comment)
    db.session.commit()
    return redirect(url_for("display_blogs"))

@app.route("/edit_comment/<int:comment_id>",methods=["POST"])
@login_required
def edit_comment(comment_id):
    comment=Comment.query.get_or_404(comment_id)
    if current_user.role!="admin" and comment.email!=current_user.email:
        flash("You can only edit your own comment!","danger")
        return redirect(url_for("display_blogs"))
    new_text=request.form["comment_text"]
    if new_text:
        comment.comment_text=new_text
        db.session.commit()
        flash("Comment updated successfully!","success")
    return redirect(url_for("display_blogs"))

@app.route("/delete_comment/<int:comment_id>",methods=["POST"])
@login_required
def delete_comment(comment_id):
    comment=Comment.query.get_or_404(comment_id)
    if current_user.role!="admin" and comment.email!=current_user.email:
        flash("You can only delete your own comment!","danger")
        return redirect(url_for("display_blogs"))
    db.session.delete(comment)
    db.session.commit()
    flash("Comment deleted successfully!","success")
    return redirect(url_for("display_blogs"))

@app.route('/categories',methods=['GET','POST'])
@login_required
def categories():
    blogs=[] 
    search_query=""
    if request.method=='POST':
        search_query=request.form['search'].strip().lower()
        blogs=Blog.query.filter(Blog.category.ilike(f"%{search_query}%")).all()
    return render_template('categories.html',blogs=blogs,search_query=search_query)

@app.route('/contact')
def contact():
    return render_template("contact.html")

@app.route('/privacy_policy')
def privacy_policy():
    return render_template("privacy_policy.html")

@app.route('/terms')
def terms():
    return render_template('privacy_policy.html')

@app.route('/editorial_policies')
def editorial_policies():
    return render_template('privacy_policy.html')

@app.route('/api/blogs', methods=['GET', 'POST'])
def api_blogs():
    if request.method == 'GET':
        blogs = Blog.query.filter_by(created_by_django=True).order_by(Blog.created_at.desc()).all()
        blogs_data = [{
            'id': blog.id,
            'title': blog.title,
            'content': blog.content,
            'author_name': blog.author_name,
            'author_email': blog.author_email,
            'category': blog.category,
        } for blog in blogs]
        return jsonify({'blogs': blogs_data})

    elif request.method == 'POST':
        data = request.json
        new_blog = Blog(
            title=data['title'],
            content=data['content'],
            author_name=data['author_name'],
            author_email=data['author_email'],
            category=data['category'],
            created_by_django=True
        )
        db.session.add(new_blog)
        db.session.commit()
        return jsonify({"message": "Blog created successfully", "id": new_blog.id}), 201

@app.route('/api/blogs/<int:blog_id>', methods=['PUT'])
def api_edit_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)

    data = request.get_json()

    blog.title = data.get('title', blog.title)
    blog.content = data.get('content', blog.content)
    blog.author_name = data.get('author_name', blog.author_name)
    blog.author_email = data.get('author_email', blog.author_email)

    db.session.commit()
    return jsonify({'message': 'Blog updated in Flask API'}), 200

@app.route('/api/blogs/<int:blog_id>', methods=['DELETE'])
def api_delete_blog(blog_id):
    blog = Blog.query.get_or_404(blog_id)
    db.session.delete(blog)
    db.session.commit()
    return jsonify({'message': 'Blog deleted from Flask API'}), 200

@app.route('/api/feedbacks', methods=['GET', 'POST'])
def api_feedbacks():
    if request.method == 'GET':
        feedbacks = Feedback.query.all()
        feedback_data = [{
            'id': fb.id,
            'first_name': fb.first_name,
            'last_name': fb.last_name,
            'email': fb.email,
            'rating': fb.rating,
            'feedback_message': fb.feedback_message
        } for fb in feedbacks]
        return jsonify({'feedbacks': feedback_data})
    
    elif request.method == 'POST':
        data = request.json
        new_feedback = Feedback(
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            email=data.get('email'),
            rating=data.get('rating'),
            feedback_message=data.get('feedback_message')
        )
        db.session.add(new_feedback)
        db.session.commit()
        return jsonify({"message": "Feedback submitted successfully"}), 201

@app.route('/signup',methods=['GET', 'POST'])
def signup():
    if request.method=='POST':
        username=request.form['username']
        email=request.form['email']
        mobileno=request.form['mobileno']
        password=request.form['password']
        existing_user=User.query.filter((User.email==email)|(User.username==username)).first()
        if existing_user:
            flash('Email or username already exists!','error')
            return redirect(url_for('signup'))
        password_hash=generate_password_hash(password)
        new_user=User(username=username,email=email,mobileno=mobileno, password_hash=password_hash)
        db.session.add(new_user)
        db.session.commit()
        flash('Account created successfully!','success')
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route("/login",methods=["GET", "POST"])
def login():
    selected_role=None
    if request.method=="POST":
        email=request.form["email"]
        password=request.form["password"]
        role=request.form.get("role")
        selected_role=role
        user=User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            if role=="admin":
                if email=="admin@gmail.com" and user.role=="admin":
                    login_user(user)
                    flash("Admin login successful!","success")
                    return redirect(url_for("index"))
                else:
                    flash("Invalid admin credentials!","danger")
                    return render_template("login.html",selected_role=selected_role)
            elif role=="user" and user.role=="user":
                login_user(user)
                flash(f"Welcome,{user.username}!","success")
                return redirect(url_for("index"))
        flash("Invalid email or password!","danger")
    return render_template("login.html",selected_role=selected_role)

if __name__=='__main__':
    app.run(debug=True)