
#initializing flask

from flask import Flask, request, jsonify , send_file , Request , abort, Blueprint
from PIL import Image, ImageDraw
from flask_sqlalchemy import SQLAlchemy 
from sqlalchemy import func
from flask_cors import CORS
from io import *
from datetime import datetime, timedelta, timezone
from werkzeug.utils import *
from flask_socketio import SocketIO, join_room, leave_room, send
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relationship
import base64
import os
import random
import logging
from sqlalchemy.exc import IntegrityError
# Your existing code follows...



# fiximg cors origin / cors policy

app = Flask(__name__)
CORS(app, origins=['http://localhost:3000', 'http://192.168.0.101'])

# connecting to sql server

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:root@localhost/kanona'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")


#regestration class component

class Reg(db.Model):
    __tablename__ = 'Reg'
    name = db.Column(db.String(100))
    username = db.Column(db.String(100), primary_key=True)
    date = db.Column(db.String(100))
    password = db.Column(db.String(100))
    email = db.Column(db.String(100), unique=True) 
    phone = db.Column(db.String(100), unique=True)

    def __init__(self, name, username, date, password, email, phone):
        self.name = name
        self.username = username
        self.date = date
        self.password = password
        self.email = email
        self.phone = phone

# userprofile table component

class UserProfile(db.Model):
    __tablename__ = 'UserProfile'
    username = db.Column(db.String(100), primary_key=True)
    bio = db.Column(db.Text)
    profile_image = db.Column(db.LargeBinary)

    def __init__(self, username, bio, profile_image):
        self.username = username
        self.bio = bio
        self.profile_image = profile_image



# login condition

@app.route('/login', methods=["POST"])
def login():
    if request.method == "POST":
        data = request.json
        if 'password' not in data or 'identifier' not in data:
            return jsonify({'error': 'Invalid request data'}), 400
        
        password = data['password']
        identifier = data['identifier']
        
        # Check if identifier is username, email, or phone
        user = Reg.query.filter((Reg.username == identifier) | (Reg.email == identifier) | (Reg.phone == identifier)).first()
        if user:
            if password == user.password:
                return jsonify({'message': 'Successfully logged in', 'username': user.username , 'email':user.email , 'phone':user.phone}), 200
            else:
                return jsonify({'error': 'Incorrect password'}), 401
        else:
            return jsonify({'error': 'User not found'}), 404

#regestration condition

@app.route('/reg', methods=['POST'])
def registration():
    if request.method == "POST":
        data = request.json
        if 'name' not in data or 'username' not in data or 'date' not in data or 'password' not in data or 'email' not in data or 'phone' not in data:
            return jsonify({'error': 'Invalid request data'}), 400
        name = data['name']
        username = data['username']
        date = data['date']
        password = data['password']
        email = data['email']
        phone = data['phone']
        
      
        if Reg.query.filter_by(phone=phone).first():
            return jsonify({'error': 'Phone number already exists'}), 409

        if Reg.query.filter_by(username=username).first():
            return jsonify({'error': 'Username already exists'}), 409
        
        
        if Reg.query.filter_by(email=email).first():
            return jsonify({'error': 'Email already exists'}), 409

        new_user = Reg(name=name, username=username, date=date, password=password, email=email, phone=phone)
        db.session.add(new_user)
        db.session.commit()
        return jsonify({'message': 'Successfully added data'}), 200
    
# condition for taking phone number

@app.route('/phone', methods=['POST'])
def phone():
    if request.method == "POST":
        data = request.json
        if 'phone' not in data:
            return jsonify({'error': 'Invalid request data'}), 400
        phone = data['phone']
        # You can implement email verification logic here
        return jsonify({'message': 'phone verified successfully', 'phone': phone}), 200
    
#condition for taking email

@app.route('/verify-email', methods=['POST'])
def verify_email():
    if request.method == "POST":
        data = request.json
        if 'email' not in data:
            return jsonify({'error': 'Invalid request data'}), 400
        email = data['email']
        # You can implement email verification logic here
        return jsonify({'message': 'Email verified successfully', 'email': email}), 200
    

# user profile table updation



@app.route('/profile/update', methods=['POST'])
def update_profile():
    if request.method == 'POST':
        username = request.form.get('username')
        bio = request.form.get('bio')
        image = request.files.get('image')
        
        user_profile = UserProfile.query.filter_by(username=username).first()
  
        if user_profile:
            if bio is not None:
                user_profile.bio = bio
            
            if image is not None:
                image_data = image.read()  # Read binary data from file
                user_profile.profile_image = image_data  # Update profile image with new data
            
            db.session.commit()
            return jsonify({'message': 'Profile updated successfully'}), 200
        else:
            # If the user profile does not exist, create a new record
            obj = UserProfile(username=username, bio=bio, profile_image=image.read() if image else None)
            db.session.add(obj)
            db.session.commit()
            return jsonify({'message': 'New profile created successfully'}), 201


# condition for fetching profile image

@app.route('/profile/image/<username>', methods=['GET'])
def get_profile_image(username):
    user_profile = UserProfile.query.filter_by(username=username).first()
    if user_profile:
        if user_profile.profile_image:  # Check if profile image exists
            return send_file(BytesIO(user_profile.profile_image), mimetype='image/jpeg', as_attachment=False, environ=request.environ)
        else:
            return jsonify({'error': 'Profile image not found'}), 404
    else:
        return jsonify({'error': 'User not found'}), 404



# condition for fetching bio
@app.route('/profile/bio/<username>', methods=['GET'])
def get_user_bio(username):
    user_profile = UserProfile.query.filter_by(username=username).first()
    if user_profile:
        return jsonify({'bio': user_profile.bio})
    else:
        return jsonify({'error': 'User not found'}), 404


    

# condition for fetching name


@app.route('/profile/name/<string:username>', methods=['GET'])
def get_user_name(username):
    user = Reg.query.filter_by(username=username).first()
    if user:
        return jsonify({'name': user.name}), 200
    else:
        return jsonify({'error': 'User not found'}), 404   
    


# Route to handle username update
@app.route('/profile/edit-username', methods=['POST'])
def edit_username():
    
    data = request.json
    current_username = data.get('currentUsername')
    new_username = data.get('newUsername')

    existing_user = Reg.query.filter_by(username=new_username).first()
    if existing_user:
        return jsonify({'error': 'Username already exists'}), 400

    
    user = Reg.query.filter_by(username=current_username).first()
    if user:
        user.username = new_username
        user_profile = UserProfile.query.filter_by(username=current_username).first()
        if user_profile:
            user_profile.username = new_username
        db.session.commit()
        return jsonify({'message': 'Username updated successfully'}), 200
    else:
        return jsonify({'error': 'User not found'}), 404



# Route to delete profile picture
@app.route('/profile/delete-image/<username>', methods=['DELETE'])
def delete_profile_image(username):
    user_profile = UserProfile.query.filter_by(username=username).first()
    if user_profile:
        user_profile.profile_image = None 
        db.session.commit()
        return jsonify({'message': 'Profile picture deleted successfully'}), 200
    else:
        return jsonify({'error': 'User not found'}), 404
    

# Route to handle name update
@app.route('/profile/edit-name', methods=['POST'])
def edit_name():
    data = request.json
    username = data.get('username')  
    new_name = data.get('newName')  

    
    user = Reg.query.filter_by(username=username).first()

    if user:
       
        user.name = new_name
        db.session.commit()
        return jsonify({'message': 'Name updated successfully'}), 200
    else:
        return jsonify({'error': 'User not found'}), 404


# route to fetch number of items 

@app.route('/profile/content-count/<username>', methods=['GET'])
def content_count(username):
    post_count = Post.query.filter_by(username=username).count()
    reel_count = Reel.query.filter_by(username=username).count()
    video_count = Video.query.filter_by(username=username).count()
    total_count = post_count + reel_count + video_count
    return jsonify({
        'postCount': post_count,
        'reelCount': reel_count,
        'videoCount': video_count,
        'totalCount': total_count
    })



# Route for checking if phone number exists
@app.route('/check-phone-existence', methods=['POST'])
def check_phone_existence():
    data = request.json
    if 'phone' not in data:
        return jsonify({'error': 'Invalid request data'}), 400
    phone = data['phone']
    
   
    user = Reg.query.filter_by(phone=phone).first()
    if user:
       
        return jsonify({'exists': True}), 200
    else:
        
        return jsonify({'exists': False}), 200


# Route for checking if email exists
@app.route('/check-email-existence', methods=['POST'])
def check_email_existence():
    data = request.json
    if 'email' not in data:
        return jsonify({'error': 'Invalid request data'}), 400
    email = data['email']
    
    
    user = Reg.query.filter_by(email=email).first()
    if user:
        
        return jsonify({'exists': True}), 200
    else:
        
        return jsonify({'exists': False}), 200



# Route for resetting password
@app.route('/reset-password', methods=['POST'])
def reset_password():
    data = request.json
    email = data.get('email')
    phone = data.get('phone')
    password = data.get('password')

   
    if not email and not phone:
        return jsonify({'error': 'Email or phone not provided'}), 400

  
    user = None
    if email:
       
        user = Reg.query.filter_by(email=email).first()
    elif phone:
       
        user = Reg.query.filter_by(phone=phone).first()

    if not user:
        return jsonify({'error': 'User not found'}), 404

    
    user.password = password
   
    db.session.commit()

    return jsonify({'message': 'Password reset successfully'}), 200

# code for getting all userames with profile pics

@app.route('/get-all-usernames', methods=['GET'])
def get_all_usernames():
    try:
       
        user_profiles = UserProfile.query.all()
        
        usernames_with_profile_pic = [{'username': profile.username, 'profile_pic': base64.b64encode(profile.profile_image).decode('utf-8')} for profile in user_profiles]
        
        return jsonify({'user_profiles': usernames_with_profile_pic})
    except Exception as e:
        return jsonify({'error': str(e)}), 500



# post conntent table creation 

class Post(db.Model):
    __tablename__= 'posts'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    post_image = db.Column(db.LargeBinary, nullable=False)
    post_title = db.Column(db.String(255))
    post_description = db.Column(db.Text)
    post_datetime = db.Column(db.DateTime, default=datetime.utcnow)
    post_location = db.Column(db.String(255))
    post_tags = db.Column(db.Text)


    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'post_title': self.post_title,
            'post_description': self.post_description,
            'post_datetime': self.post_datetime.isoformat(), 
            'post_location': self.post_location,
            'post_tags': self.post_tags
           
        }

# post update 

@app.route('/update-post', methods=['POST'])
def update_post():
    if request.method == 'POST':
        username = request.form.get('username')
        post_image = request.files.get('post_image')
        post_title = request.form.get('post_title')
        post_description = request.form.get('post_description')
        post_location = request.form.get('post_location')
        post_tags = request.form.get('post_tags')

        if not post_image:
            return jsonify({'error': 'Post image is required'}), 400

        if post_image:
            post_image_data = post_image.read()
        else:
            post_image_data = None

        new_post = Post(username=username,
                        post_image=post_image_data,
                        post_title=post_title,
                        post_description=post_description,
                        post_location=post_location,
                        post_tags=post_tags)

        try:
            # Add the new post to the database
            db.session.add(new_post)
            db.session.commit()
            return jsonify({'message': 'Post updated successfully'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Failed to update post', 'details': str(e)}), 500




# get all posts with similar username 

@app.route('/get-posts-by-username', methods=['GET'])
def get_posts_by_username():
   
    username = request.args.get('username')

    posts = Post.query.filter_by(username=username).all()

    if posts:
        posts_data = [{'id': post.id, 'post_title': post.post_title, 'post_image': base64.b64encode(post.post_image).decode('utf-8'), 'post_description': post.post_description, 'post_datetime': post.post_datetime,'post_tags':post.post_tags} for post in posts]
        return jsonify({'posts': posts_data}), 200
    else:
        return jsonify({'error': 'No posts found for this username'}), 404




# code to get the post which we have clicked
@app.route('/get-post/<int:post_id>', methods=['GET'])
def get_post(post_id):
    post = Post.query.get(post_id)
    if post:
        post_data = {
            'id': post.id,
            'username': post.username,
            **post.to_dict(),
            'post_image': base64.b64encode(post.post_image).decode('utf-8')
        }
        return jsonify({'post': post_data})
    else:
        return jsonify({'error': 'Post not found'}), 404


#route to get all posts

@app.route('/get-all-posts', methods=['GET'])
def get_all_posts():
    try:
        posts = Post.query.all()
        posts_data = [{
            'id': post.id,
            'username': post.username,
            'post_title': post.post_title,
            'post_description': post.post_description,
            'post_datetime': post.post_datetime.isoformat(),
            'post_image': base64.b64encode(post.post_image).decode('utf-8'),
            'post_tags':post.post_tags
        } for post in posts]
        return jsonify({'posts': posts_data}), 200
    except Exception as e:
        return jsonify({'error': 'Failed to fetch posts', 'details': str(e)}), 500




#delete the piost whhich we have clicked
@app.route('/delete-post/<int:post_id>', methods=['DELETE'])
def delete_post(post_id):
    post = Post.query.get(post_id)
    if post:
        try:
            db.session.delete(post)
            db.session.commit()
            return jsonify({'message': 'Post deleted successfully'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Failed to delete post', 'details': str(e)}), 500
    else:
        return jsonify({'error': 'Post not found'}), 404


# reels table creation 
class Reel(db.Model):
    __tablename__ = 'reels'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    reel = db.Column(db.LargeBinary, nullable=False)
    reel_title = db.Column(db.String(255))
    reel_description = db.Column(db.Text)
    reel_location = db.Column(db.String(255))
    reel_creation_datetime = db.Column(db.DateTime, default=datetime.utcnow)
    reel_tags = db.Column(db.Text) 
   
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'reel_title': self.reel_title,
            'reel_description': self.reel_description,
            'reel_location': self.reel_location,
            'reel_creation_datetime': self.reel_creation_datetime.isoformat(),  
            'reel_tags': self.reel_tags
        }


# Route to update reels
@app.route('/update-reel', methods=['POST'])
def update_reel():
    if request.method == 'POST':
        username = request.form.get('username')
        reel_video = request.files.get('reel_video')
        reel_title = request.form.get('reel_title')
        reel_description = request.form.get('reel_description')
        reel_location = request.form.get('reel_location')
        reel_tags = request.form.get('reel_tags') 

      
        if not reel_video:
            return jsonify({'error': 'Reel video is required'}), 400

       
        if reel_video.content_length > 250 * 1024 * 1024:
            return jsonify({'error': 'Reel video size exceeds the limit of 250 MB'}), 400

       
        reel_video_data = reel_video.read()

       
        new_reel = Reel(username=username,
                        reel=reel_video_data,  
                        reel_title=reel_title,
                        reel_description=reel_description,
                        reel_location=reel_location,
                        reel_tags=reel_tags)

        try:
           
            db.session.add(new_reel)
            db.session.commit()
            return jsonify({'message': 'Reel updated successfully'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Failed to update reel', 'details': str(e)}), 500



# Route to get all reels data by username
@app.route('/get-reels-by-username', methods=['GET'])
def get_reels_by_username():
    username = request.args.get('username')
    reels = Reel.query.filter_by(username=username).all()
    if reels:
        reels_data = [{'id': reel.id, 'username': reel.username, 'reel_title': reel.reel_title, 'reel_description': reel.reel_description, 'reel_location': reel.reel_location, 'reel_creation_datetime': reel.reel_creation_datetime.isoformat(), 'reel': base64.b64encode(reel.reel).decode('utf-8') ,'reel_tags': reel.reel_tags} for reel in reels]
        return jsonify({'reels': reels_data}), 200
    else:
        return jsonify({'error': 'No reels found for this username'}), 404




# Route to get a specific reel by ID
@app.route('/get-reel/<int:reel_id>', methods=['GET'])
def get_reel(reel_id):
    reel = Reel.query.get(reel_id)
    if reel:
        reel_data = {
            'id': reel.id,
            'username': reel.username,
            **reel.to_dict(),
            'reel': base64.b64encode(reel.reel).decode('utf-8')
        }
        return jsonify({'reel': reel_data})
    else:
        return jsonify({'error': 'Reel not found'}), 404



# Route to fetch all the reels in the entire database
@app.route('/get-all-reels', methods=['GET'])
def get_all_reels():
    try:
        reels = Reel.query.all()
        reels_data = [{
            'id': reel.id,
            'username': reel.username,
            'reel_title': reel.reel_title,
            'reel_description': reel.reel_description,
            'reel_creation_datetime': reel.reel_creation_datetime.isoformat(),
            'reel': base64.b64encode(reel.reel).decode('utf-8'),
            'reel_tags': reel.reel_tags  
        } for reel in reels]
        return jsonify({'reels': reels_data}), 200
    except Exception as e:
        return jsonify({'error': 'Failed to fetch reels', 'details': str(e)}), 500




# delete the reel which we have clicked
@app.route('/delete-reel/<int:reel_id>', methods=['DELETE'])
def delete_reel(reel_id):
    reel = Reel.query.get(reel_id)
    if reel:
        try:
            db.session.delete(reel)
            db.session.commit()
            return jsonify({'message': 'Reel deleted successfully'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Failed to delete reel', 'details': str(e)}), 500
    else:
        return jsonify({'error': 'Reel not found'}), 404



# videos table creation 
class Video(db.Model):
    __tablename__ = 'videos'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    video = db.Column(db.LargeBinary, nullable=False)  # Binary data of the video file
    video_title = db.Column(db.String(255))
    video_description = db.Column(db.Text)
    video_location = db.Column(db.String(255))
    video_creation_datetime = db.Column(db.DateTime, default=datetime.utcnow)
    video_tags = db.Column(db.Text)
    thumbnail = db.Column(db.LargeBinary, nullable=True)
   
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'video_title': self.video_title,
            'video_description': self.video_description,
            'video_location': self.video_location,
            'video_creation_datetime': self.video_creation_datetime.isoformat(),
            'video_tags': self.video_tags,
        }

# Updating videos table
# Updated route to handle video and thumbnail uploads
@app.route('/update-video', methods=['POST'])
def update_video():
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            video_file = request.files.get('video_file')
            video_title = request.form.get('video_title')
            video_description = request.form.get('video_description')
            video_location = request.form.get('video_location')
            video_tags = request.form.get('video_tags')
            thumbnail = request.files.get('thumbnail')  # Ensure this matches 'thumbnail' in FormData

            if not video_file:
                return jsonify({'error': 'Video file is required'}), 400

            video_data = video_file.read()
            thumbnail_data = thumbnail.read() if thumbnail else None

            new_video = Video(username=username,
                              video=video_data,
                              video_title=video_title,
                              video_description=video_description,
                              video_location=video_location,
                              video_tags=video_tags,
                              thumbnail=thumbnail_data)  # Ensure to use thumbnail_data here

            db.session.add(new_video)
            db.session.commit()

            return jsonify({'message': 'Video uploaded successfully'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Failed to upload video', 'details': str(e)}), 500



# Route to get all videos data by username
@app.route('/get-videos-by-username', methods=['GET'])
def get_videos_by_username():
    username = request.args.get('username')
    videos = Video.query.filter_by(username=username).all()
    if videos:
        videos_data = [{'id': video.id, 'username': video.username, 'video_title': video.video_title, 'video_description': video.video_description, 'video_location': video.video_location, 'video_creation_datetime': video.video_creation_datetime.isoformat(), 'video': base64.b64encode(video.video).decode('utf-8'), 'video_tags': video.video_tags, 'thumbnail': base64.b64encode(video.thumbnail).decode('utf-8') if video.thumbnail else None} for video in videos]
        return jsonify({'videos': videos_data}), 200
    else:
        return jsonify({'error': 'No videos found for this username'}), 404

# Route to get a specific video by ID
@app.route('/get-video/<int:video_id>', methods=['GET'])
def get_video(video_id):
    video = Video.query.get(video_id)
    if video:
        video_data = {
            'id': video.id,
            'username': video.username,
            **video.to_dict(),
            'video': base64.b64encode(video.video).decode('utf-8'),
            'thumbnail': base64.b64encode(video.thumbnail).decode('utf-8') if video.thumbnail else None
        }
        return jsonify({'video': video_data})
    else:
        return jsonify({'error': 'Video not found'}), 404

# Get all videos
@app.route('/get-all-videos', methods=['GET'])
def get_all_videos():
    try:
        videos = Video.query.all()
        videos_data = [{
            'id': video.id,
            'username': video.username,
            'video_title': video.video_title,
            'video_description': video.video_description,
            'video_creation_datetime': video.video_creation_datetime.isoformat(),
            'video': base64.b64encode(video.video).decode('utf-8'),
            'video_tags': video.video_tags,
            'thumbnail': base64.b64encode(video.thumbnail).decode('utf-8') if video.thumbnail else None
        } for video in videos]
        return jsonify({'videos': videos_data}), 200
    except Exception as e:
        return jsonify({'error': 'Failed to fetch videos', 'details': str(e)}), 500

# Delete the video which we have clicked
@app.route('/delete-video/<int:video_id>', methods=['DELETE'])
def delete_video(video_id):
    video = Video.query.get(video_id)
    if video:
        try:
            db.session.delete(video)
            db.session.commit()
            return jsonify({'message': 'Video deleted successfully'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': 'Failed to delete video', 'details': str(e)}), 500
    else:
        return jsonify({'error': 'Video not found'}), 404







@app.route('/get-content/<int:content_id>/<content_type>', methods=['GET'])
def get_content_by_id_and_type(content_id, content_type):
    try:
        if content_type == 'Post':
            content_item = Post.query.get(content_id)
        elif content_type == 'Reel':
            content_item = Reel.query.get(content_id)
        elif content_type == 'Video':
            content_item = Video.query.get(content_id)
        else:
            return jsonify({'error': 'Invalid content type'}), 400

        if not content_item:
            return jsonify({'error': 'Content not found'}), 404

        formatted_item = {
            'content_id': content_item.id,
            'username': content_item.username,
            'content_type': content_type,
            'title': getattr(content_item, 'post_title', getattr(content_item, 'reel_title', getattr(content_item, 'video_title', ''))),
            'description': getattr(content_item, 'post_description', getattr(content_item, 'reel_description', getattr(content_item, 'video_description', ''))),
            'date': getattr(content_item, 'post_datetime', getattr(content_item, 'reel_creation_datetime', getattr(content_item, 'video_creation_datetime', ''))).isoformat()
        }

        if hasattr(content_item, 'post_image'):
            formatted_item['post_image'] = base64.b64encode(content_item.post_image).decode('utf-8')
        if hasattr(content_item, 'reel'):
            formatted_item['reel'] = base64.b64encode(content_item.reel).decode('utf-8')
        if hasattr(content_item, 'video'):
            formatted_item['video'] = base64.b64encode(content_item.video).decode('utf-8')

        return jsonify(formatted_item), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500




# Route to get all content in a random order
@app.route('/get-all-content', methods=['GET'])
def get_all_content():
    try:
        # Retrieve all posts, reels, and videos from their respective tables
        all_posts = Post.query.all()
        all_reels = Reel.query.all()
        all_videos = Video.query.all()
        
        all_content = all_posts + all_reels + all_videos
   
        random.shuffle(all_content)
        
        formatted_content = []
        
        # Iterate over the shuffled list to format the content
        for index, item in enumerate(all_content):
            if isinstance(item, Post):
                content_type = 'Post'
            elif isinstance(item, Reel):
                content_type = 'Reel'
            elif isinstance(item, Video):
                content_type = 'Video'
            else:
                continue  
            
            content_id = item.id  # Assign a unique identifier to each content item
            
            formatted_item = {
                'content_id': content_id,
                'username': item.username,
                'content_type': content_type,
                'title': item.post_title if hasattr(item, 'post_title') else item.reel_title if hasattr(item, 'reel_title') else item.video_title,
                'description': item.post_description if hasattr(item, 'post_description') else item.reel_description if hasattr(item, 'reel_description') else item.video_description,
                'date': item.post_datetime.isoformat() if hasattr(item, 'post_datetime') else item.reel_creation_datetime.isoformat() if hasattr(item, 'reel_creation_datetime') else item.video_creation_datetime.isoformat()
            }
            
            if hasattr(item, 'post_image'):
                formatted_item['post_image'] = base64.b64encode(item.post_image).decode('utf-8')
            if hasattr(item, 'reel'):
                formatted_item['reel'] = base64.b64encode(item.reel).decode('utf-8')
            if hasattr(item, 'video'):
                formatted_item['video'] = base64.b64encode(item.video).decode('utf-8')
            
            formatted_content.append(formatted_item)
        
        return jsonify({'content': formatted_content}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500





# New Route to get content by type
@app.route('/get-content-by-type/<content_type>', methods=['GET'])
def get_content_by_type(content_type):
    try:
        if content_type == 'Post':
            content_items = Post.query.all()
        elif content_type == 'Reel':
            content_items = Reel.query.all()
        elif content_type == 'Video':
            content_items = Video.query.all()
        else:
            return jsonify({'error': 'Invalid content type'}), 400
        
        formatted_content = []
        
        for item in content_items:
            content_id = item.id
            formatted_item = {
                'content_id': content_id,
                'username': item.username,
                'content_type': content_type,
                'title': getattr(item, 'post_title', getattr(item, 'reel_title', getattr(item, 'video_title', ''))),
                'description': getattr(item, 'post_description', getattr(item, 'reel_description', getattr(item, 'video_description', ''))),
                'date': getattr(item, 'post_datetime', getattr(item, 'reel_creation_datetime', getattr(item, 'video_creation_datetime', ''))).isoformat()
            }
            
            if hasattr(item, 'post_image'):
                formatted_item['post_image'] = base64.b64encode(item.post_image).decode('utf-8')
            if hasattr(item, 'reel'):
                formatted_item['reel'] = base64.b64encode(item.reel).decode('utf-8')
            if hasattr(item, 'video'):
                formatted_item['video'] = base64.b64encode(item.video).decode('utf-8')
            
            formatted_content.append(formatted_item)
        
        return jsonify({'content': formatted_content}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500




#likes table creation

class Like(db.Model):
    __tablename__ = 'likes'
    id = db.Column(db.Integer, primary_key=True)
    content_type = db.Column(db.String(255))
    content_id = db.Column(db.Integer)
    posted_by = db.Column(db.String(255))
    liked_by = db.Column(db.String(255))  # Store username directly instead of JSON list
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    def __repr__(self):
        return f"Like(id={self.id}, content_type={self.content_type}, content_id={self.content_id}, posted_by={self.posted_by}, liked_by={self.liked_by}, created_at={self.created_at})"

    def to_dict(self):
        return {
            'id': self.id,
            'content_type': self.content_type,
            'content_id': self.content_id,
            'posted_by': self.posted_by,
            'liked_by': self.liked_by,
            'created_at': self.created_at.isoformat(),  # Convert datetime to ISO format
        }
    

    
   
# Function to get likes count for a specific content
def get_likes_count_for_content(content_id, content_type):
    likes_count = Like.query.filter_by(content_id=content_id, content_type=content_type).count()
    return likes_count

# Your route to handle liking / unliking content
@app.route('/like', methods=['POST'])
def like_content():
    data = request.json
    content_type = data.get('content_type')
    content_id = data.get('content_id')
    posted_by = data.get('posted_by')
    liked_by = data.get('liked_by')

    # Check if the user has already liked the content
    existing_like = Like.query.filter_by(content_id=content_id, liked_by=liked_by).first()

    if existing_like:
        # Unlike the content
        db.session.delete(existing_like)
        db.session.commit()
    else:
        # Like the content
        new_like = Like(content_type=content_type, content_id=content_id, posted_by=posted_by, liked_by=liked_by)
        db.session.add(new_like)
        db.session.commit()

    # Retrieve the updated likes count for the content
    likes_count = get_likes_count_for_content(content_id, content_type)
    
    return jsonify({"message": "Liked successfully", "likes": likes_count})

# Route to get the likes count for all content
@app.route('/likes/count')
def get_likes_count():
    likes_count_query = db.session.query(Like.content_id, Like.content_type, func.count(Like.id)).group_by(Like.content_id, Like.content_type).all()
    likes_count = {(content_id, content_type): count for content_id, content_type, count in likes_count_query}
    return jsonify(likes_count)

# Route to check liked state for a user
@app.route('/like/check', methods=['POST'])
def check_liked_state():
    data = request.json
    content_id = data.get('content_id')
    liked_by = data.get('liked_by')

    # Check if the user has liked the content
    existing_like = Like.query.filter_by(content_id=content_id, liked_by=liked_by).first()

    if existing_like:
        return jsonify({'isLiked': True})
    else:
        return jsonify({'isLiked': False})


# Your route to get likes count and liked state for multiple videos
@app.route('/likes/status', methods=['POST'])
def get_likes_status():
    data = request.json
    content_ids = data.get('content_ids')
    liked_by = data.get('liked_by')

    likes_status = {}
    for content_id in content_ids:
        likes_count = get_likes_count_for_content(content_id, 'Video')
        is_liked = Like.query.filter_by(content_id=content_id, liked_by=liked_by).first() is not None
        likes_status[content_id] = {'likes': likes_count, 'isLiked': is_liked}

    return jsonify(likes_status)










class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    content_type = db.Column(db.String(255))
    content_id = db.Column(db.Integer)
    parent_id = db.Column(db.Integer, db.ForeignKey('comments.id'), nullable=True)  # For replies
    posted_by = db.Column(db.String(255))
    comment = db.Column(db.Text)
    commented_by = db.Column(db.String(255))
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)
    
    def __repr__(self):
        return f"Comment(id={self.id}, content_type={self.content_type}, content_id={self.content_id}, parent_id={self.parent_id}, posted_by={self.posted_by}, comment={self.comment}, commented_by={self.commented_by}, created_at={self.created_at})"

    def to_dict(self):
        return {
            'id': self.id,
            'content_type': self.content_type,
            'content_id': self.content_id,
            'parent_id': self.parent_id,
            'posted_by': self.posted_by,
            'comment': self.comment,
            'commented_by': self.commented_by,
            'created_at': self.created_at.isoformat(),
          
        }


@app.route('/comment/reply', methods=['POST'])
def add_reply():
    data = request.json
    content_type = data.get('content_type')
    content_id = data.get('content_id')
    parent_id = data.get('parent_id')
    posted_by = data.get('posted_by')
    comment_text = data.get('comment')
    commented_by = data.get('commented_by')

    new_comment = Comment(content_type=content_type, content_id=content_id, parent_id=parent_id, posted_by=posted_by, comment=comment_text, commented_by=commented_by)
    db.session.add(new_comment)
    db.session.commit()

    return jsonify({"message": "Reply added successfully"})





# Route to get comments for specific content with like information
@app.route('/comments/<content_type>/<int:content_id>')
def get_comments(content_type, content_id):
    comments = Comment.query.filter_by(content_type=content_type, content_id=content_id).all()
    comments_data = []
    for comment in comments:
        comment_data = comment.to_dict()
        comment_data['likes'] = get_comment_likes(comment.id)
        comment_data['liked_by_user'] = is_comment_liked_by_user(comment.id, request.args.get('username'))
        comments_data.append(comment_data)
    return jsonify(comments_data)

def is_comment_liked_by_user(comment_id, username):
    if not username:
        return False
    return CommentLike.query.filter_by(comment_id=comment_id, liked_by=username).count() > 0


# Route to add comment
@app.route('/comment', methods=['POST'])
def add_comment():
    data = request.json
    content_type = data.get('content_type')
    content_id = data.get('content_id')
    posted_by = data.get('posted_by')
    comment_text = data.get('comment')
    commented_by = data.get('commented_by')

    new_comment = Comment(content_type=content_type, content_id=content_id, posted_by=posted_by, comment=comment_text, commented_by=commented_by)
    db.session.add(new_comment)
    db.session.commit()

    return jsonify({"message": "Comment added successfully"})



# Route to delete a comment by ID
@app.route('/comment/<int:comment_id>', methods=['DELETE'])
def delete_comment(comment_id):
    comment = Comment.query.get(comment_id)
    if comment:
        current_username = request.json.get('username')
        if comment.commented_by == current_username or comment.posted_by == current_username:
            db.session.delete(comment)
            db.session.commit()
            return jsonify({"message": "Comment deleted successfully"})
        else:
            return jsonify({"error": "Not authorized to delete this comment"}), 403
    else:
        return jsonify({"error": "Comment not found"}), 404





class CommentLike(db.Model):
    __tablename__ = 'comment_likes'
    id = db.Column(db.Integer, primary_key=True)
    comment_id = db.Column(db.Integer, nullable=False)
    liked_by = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    def __repr__(self):
        return f"CommentLike(id={self.id}, comment_id={self.comment_id}, liked_by={self.liked_by}, created_at={self.created_at})"

@app.route('/like/comment', methods=['POST'])
def like_comment():
    data = request.json
    comment_id = data.get('comment_id')
    liked_by = data.get('liked_by')
    
    if not comment_id or not liked_by:
        return jsonify({"error": "Invalid data"}), 400
    
    comment = Comment.query.get(comment_id)
    if not comment:
        return jsonify({"error": "Comment not found"}), 404

    existing_like = CommentLike.query.filter_by(comment_id=comment_id, liked_by=liked_by).first()

    if existing_like:
        db.session.delete(existing_like)
        db.session.commit()
        return jsonify({"message": "Comment like removed successfully", "likes": get_comment_likes(comment_id)})

    new_like = CommentLike(comment_id=comment_id, liked_by=liked_by)
    db.session.add(new_like)
    db.session.commit()

    return jsonify({"message": "Comment liked successfully", "likes": get_comment_likes(comment_id)})

def get_comment_likes(comment_id):
    return CommentLike.query.filter_by(comment_id=comment_id).count()
    
@app.route('/like/comment/check', methods=['POST'])
def check_comment_like():
    data = request.get_json()
    comment_id = data.get('comment_id')
    liked_by = data.get('liked_by')

    # Query to check if the comment is liked by the user
    liked = CommentLike.query.filter_by(comment_id=comment_id, liked_by=liked_by).first() is not None
    
    return jsonify({'isLiked': liked})




class Follower(db.Model):
    __tablename__ = 'followers'
    id = db.Column(db.Integer, primary_key=True)
    follower = db.Column(db.String(255), nullable=False)
    followed = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.TIMESTAMP, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'follower': self.follower,
            'followed': self.followed,
            'created_at': self.created_at.isoformat(),
        }

@app.route('/follow', methods=['POST'])
def follow_user():
    data = request.json
    follower = data.get('follower')
    followed = data.get('followed')

    existing_follow = Follower.query.filter_by(follower=follower, followed=followed).first()

    if existing_follow:
        db.session.delete(existing_follow)
        db.session.commit()
        return jsonify({'message': 'Unfollowed successfully', 'isFollowing': False})
    else:
        new_follow = Follower(follower=follower, followed=followed)
        db.session.add(new_follow)
        db.session.commit()
        return jsonify({'message': 'Followed successfully', 'isFollowing': True})

@app.route('/follow/check', methods=['POST'])
def check_follow_state():
    data = request.json
    follower = data.get('follower')
    followed = data.get('followed')

    existing_follow = Follower.query.filter_by(follower=follower, followed=followed).first()

    if existing_follow:
        return jsonify({'isFollowing': True})
    else:
        return jsonify({'isFollowing': False})



# New endpoint to fetch follower count for a given username
@app.route('/profile/followers-count/<username>', methods=['GET'])
def followers_count(username):
    count = Follower.query.filter_by(followed=username).count()
    return jsonify({'followersCount': count})

# New endpoint to fetch following count for a given username
@app.route('/profile/following-count/<username>', methods=['GET'])
def following_count(username):
    count = Follower.query.filter_by(follower=username).count()
    return jsonify({'followingCount': count})


@app.route('/following', methods=['GET'])
def get_following_users():
    username = request.args.get('username')
    if not username:
        return jsonify({'error': 'Username is required'}), 400

    following = Follower.query.filter_by(follower=username).all()
    following_usernames = [follow.followed for follow in following]
    
    return jsonify({'following': following_usernames})


class Chatroom(db.Model):
    __tablename__ = 'chatrooms'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    is_group = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    members = relationship('Reg', secondary='chatroom_members')

    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'is_group': self.is_group,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'members': [member.username for member in self.members]
        }

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chatroom_id = db.Column(db.Integer, nullable=False)
    sender_id = db.Column(db.String(50), nullable=False)
    receiver_id = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    content_type = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)

    def serialize(self):
        return {
            'id': self.id,
            'chatroom_id': self.chatroom_id,
            'sender_id': self.sender_id,
            'receiver_id': self.receiver_id,
            'content': self.content,
            'content_type': self.content_type,
            'timestamp': self.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        }


class ChatroomMember(db.Model):
    __tablename__ = 'chatroom_members'
    id = db.Column(db.Integer, primary_key=True)
    chatroom_id = db.Column(db.Integer, ForeignKey('chatrooms.id'), nullable=False)
    user_id = db.Column(db.String(100), ForeignKey('Reg.username'), nullable=False)

# Routes

@app.route('/create-group', methods=['POST'])
def create_group():
    data = request.json
    group_name = data.get('groupName')
    group_members = data.get('groupMembers')

    chatroom = Chatroom(name=group_name, is_group=True)
    db.session.add(chatroom)
    db.session.commit()

    for member in group_members:
        chatroom_member = ChatroomMember(chatroom_id=chatroom.id, user_id=member)
        db.session.add(chatroom_member)
    db.session.commit()

    return jsonify({'message': 'Group created successfully'}), 201

@app.route('/chatrooms/<username>', methods=['GET'])
def get_chatrooms(username):
    chatrooms = Chatroom.query.join(ChatroomMember).filter(ChatroomMember.user_id == username).all()
    serialized_chatrooms = [chatroom.serialize() for chatroom in chatrooms]
    return jsonify({'chatrooms': serialized_chatrooms})

@app.route('/messages', methods=['POST'])
def send_message():
    data = request.json
    chatroom_id = data.get('chatroom_id')
    sender_id = data.get('sender_id')
    receiver_id = data.get('receiver_id')  # Add this line
    content = data.get('content')
    content_type = data.get('content_type')

    if not chatroom_id or not sender_id or not receiver_id or not content or not content_type:
        return jsonify({'error': 'Missing required fields'}), 400

    message = Message(chatroom_id=chatroom_id, sender_id=sender_id, receiver_id=receiver_id, content=content, content_type=content_type)  # Modify this line
    db.session.add(message)
    db.session.commit()

    return jsonify({'message': 'Message sent successfully'}), 201


@app.route('/messages/<username>', methods=['GET'])
def get_messages(username):
    current_user = request.args.get('current_user')
    messages = Message.query.filter(
        ((Message.sender_id == current_user) & (Message.receiver_id == username)) |
        ((Message.sender_id == username) & (Message.receiver_id == current_user))
    ).order_by(Message.timestamp).all()
    serialized_messages = [message.serialize() for message in messages]
    return jsonify({'messages': serialized_messages})

@app.route('/share-content', methods=['POST'])
def share_content():
    data = request.json
    chatroom_id = data.get('chatroom_id')
    sender_id = data.get('sender_id')
    receiver_id = data.get('receiver_id')
    content_id = data.get('content_id')
    content_type = data.get('content_type')

    if not chatroom_id or not sender_id or not receiver_id or not content_id or not content_type:
        return jsonify({'error': 'Missing required fields'}), 400

    content_link = f"/contentdetails/{content_id}/{content_type}"
    message = Message(
        chatroom_id=chatroom_id,
        sender_id=sender_id,
        receiver_id=receiver_id,
        content=content_link,
        content_type=content_type
    )
    db.session.add(message)
    db.session.commit()

    return jsonify({'message': 'Content shared successfully'}), 201




stories_bp = Blueprint('stories', __name__)

class Story(db.Model):
    __tablename__ = 'stories'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), nullable=False)
    story_data = db.Column(db.LargeBinary, nullable=False)
    is_new = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expiry_timestamp = db.Column(db.DateTime, default=datetime.utcnow() + timedelta(days=1))

    def __repr__(self):
        return f"<Story(username='{self.username}')>"

# Endpoint to add a new story
@stories_bp.route('/add-story', methods=['POST'])
def add_story():
    try:
        username = request.form.get('username')
        story_data = request.files['story_data'].read()

        new_story = Story(username=username, story_data=story_data)
        db.session.add(new_story)
        db.session.commit()

        return jsonify({'message': 'Story added successfully!'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Endpoint to get all stories
@stories_bp.route('/get-stories', methods=['GET'])
def get_stories():
    try:
        stories = Story.query.all()
        return jsonify([{
            'id': story.id,
            'username': story.username,
            'created_at': story.created_at.strftime('%Y-%m-%d %H:%M:%S'),
            'is_new': story.is_new,
            'expiry_timestamp': story.expiry_timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            'story_data': base64.b64encode(story.story_data).decode('utf-8')  # Convert blob to base64 string
        } for story in stories])
    except Exception as e:
        return jsonify({'error': str(e)}), 500





class Share(db.Model):
    __tablename__="shares"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    movie_name = db.Column(db.Text, nullable=False)
    movie_description = db.Column(db.Text)
    area_of_releasing = db.Column(db.Text)
    number_of_theatres = db.Column(db.Integer)
    number_of_shows_per_day = db.Column(db.Integer)
    additional_information = db.Column(db.Text)
    total_expenditure = db.Column(db.Numeric(10, 2))
    number_of_shares_divided = db.Column(db.Integer)
    cost_of_each_share = db.Column(db.Numeric(10, 2))
    number_of_shares_holding = db.Column(db.Integer)
    number_of_shares_released = db.Column(db.Integer)
    number_of_shares_limited = db.Column(db.Integer)
    share_validity = db.Column(db.Date)
    poster = db.Column(db.LargeBinary, nullable=False)
    


class Booking(db.Model):
    __tablename__ = 'bookings'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), nullable=False)
    share_id = db.Column(db.Integer, db.ForeignKey('shares.id'), nullable=False)
    number_of_shares = db.Column(db.Integer, nullable=False)

    

@app.route('/upload_share', methods=['POST'])
def upload_share():
    if 'poster' not in request.files:
        return jsonify({'message': 'No file part'}), 400
    file = request.files['poster']
    if file.filename == '':
        return jsonify({'message': 'No selected file'}), 400

    try:
        # Save file as binary
        poster_binary = file.read()

        data = request.form  # Use request.form to get other form data
        new_share = Share(
            username=data['username'],
            movie_name=data['movie_name'],
            movie_description=data.get('movie_description'),
            area_of_releasing=data.get('area_of_releasing'),
            number_of_theatres=data.get('number_of_theatres'),
            number_of_shows_per_day=data.get('number_of_shows_per_day'),
            additional_information=data.get('additional_information'),
            total_expenditure=data.get('total_expenditure'),
            number_of_shares_divided=data.get('number_of_shares_divided'),
            cost_of_each_share=data.get('cost_of_each_share'),
            number_of_shares_holding=data.get('number_of_shares_holding'),
            number_of_shares_released=data.get('number_of_shares_released'),
            number_of_shares_limited=data.get('number_of_shares_limited'),
            share_validity=datetime.strptime(data.get('share_validity'), '%Y-%m-%d').date(),
            poster=poster_binary
        )
        db.session.add(new_share)
        db.session.commit()
        return jsonify({'message': 'Share uploaded successfully'}), 200
    except IntegrityError:
        db.session.rollback()
        return jsonify({'message': 'Error uploading share'}), 400

@app.route('/view_share_status/<username>', methods=['GET'])
def view_share_status(username):
    shares = Share.query.filter_by(username=username).all()
    results = []
    for share in shares:
        bookings = Booking.query.filter_by(share_id=share.id).all()
        sold_shares = sum(booking.number_of_shares for booking in bookings)
        remaining_shares = share.number_of_shares_holding - sold_shares
        results.append({
            'movie_name': share.movie_name,
            'total_shares': share.number_of_shares_divided,
            'released': share.number_of_shares_released,
            'holding': share.number_of_shares_holding,
            'sold_shares': sold_shares,
            'remaining_shares': remaining_shares,
            'validity': share.share_validity,
            'additional_information': share.additional_information,
            'bookings': [{'username': b.username, 'number_of_shares': b.number_of_shares} for b in bookings]
        })
    return jsonify(results), 200


@app.route('/buy_share', methods=['POST'])
def buy_share():
    data = request.json
    share_id = int(data.get('share_id'))
    number_of_shares = int(data.get('number_of_shares'))
    username = data.get('username')
    
    share = Share.query.get(share_id)
    if not share:
        return jsonify({'message': 'Share not found'}), 404
    
    bookings = Booking.query.filter_by(share_id=share_id).all()
    sold_shares = sum(booking.number_of_shares for booking in bookings)
    remaining_shares = share.number_of_shares_holding - sold_shares
    
    if number_of_shares > remaining_shares:
        return jsonify({'message': 'Not enough shares available'}), 400
    
    new_booking = Booking(username=username, share_id=share_id, number_of_shares=number_of_shares)
    db.session.add(new_booking)
    db.session.commit()
    
    return jsonify({'message': 'Share bought successfully'}), 201


@app.route('/shares', methods=['GET'])
def get_all_shares():
    shares = Share.query.all()
    results = []
    for share in shares:
        results.append({
            'id': share.id,
            'movie_name': share.movie_name,
            'total_shares': share.number_of_shares_divided,
            'released': share.number_of_shares_released,
            'holding': share.number_of_shares_holding,
            'validity': share.share_validity,
            'number_of_shares_limited': share.number_of_shares_limited
        })
    return jsonify(results), 200


@app.route('/profile/portfolio/<username>', methods=['GET'])
def get_portfolio(username):
    # Query all shares for the given username
    shares = Share.query.filter_by(username=username).all()
    
    # Process shares and compile the response
    results = []
    for share in shares:
        bookings = Booking.query.filter_by(share_id=share.id).all()
        sold_shares = sum(booking.number_of_shares for booking in bookings)
        remaining_shares = share.number_of_shares_holding - sold_shares
        
        # Convert binary poster to base64 string for JSON compatibility
        poster_base64 = base64.b64encode(share.poster).decode('utf-8') if share.poster else None
        
        results.append({
            'id': share.id,
            'movie_name': share.movie_name,
            'movie_description': share.movie_description,
            'area_of_releasing': share.area_of_releasing,
            'number_of_theatres': share.number_of_theatres,
            'number_of_shows_per_day': share.number_of_shows_per_day,
            'additional_information': share.additional_information,
            'total_expenditure': str(share.total_expenditure),  # Convert to string for JSON compatibility
            'number_of_shares_divided': share.number_of_shares_divided,
            'cost_of_each_share': str(share.cost_of_each_share),  # Convert to string for JSON compatibility
            'number_of_shares_holding': share.number_of_shares_holding,
            'number_of_shares_released': share.number_of_shares_released,
            'number_of_shares_limited': share.number_of_shares_limited,
            'share_validity': share.share_validity.strftime('%Y-%m-%d') if share.share_validity else None,
            'poster': poster_base64  # Base64 encoded poster
        })
    
    return jsonify(results), 200



if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True, port=9889)
