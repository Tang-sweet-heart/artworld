"""
艺术与世界 - 完整主程序文件 (app.py)
完整版：包含所有必要的路由，支持完整的用户功能。
"""

# ========== 1. 导入所有需要的库 ==========
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
import json
import openai  # 用于AI搜索
import hashlib
import time

# ========== 2. 创建Flask应用和数据库实例 ==========
app = Flask(__name__)

app.config['SECRET_KEY'] = 'lidd0929kiki'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///artworld.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 限制上传文件大小为5MB

db = SQLAlchemy(app)

# ========== 3. 配置AI模型（无问芯穹）==========
client = openai.OpenAI(
    api_key="sk-g64qft7w2e7xd43t",
    base_url="https://cloud.infini-ai.com/maas/v1"
)

# ========== 4. 数据库表结构 ==========
class User(db.Model):
    """用户表"""
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    avatar = db.Column(db.String(200), default='default.jpg')
    is_reviewer = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 添加这些新字段
    real_name = db.Column(db.String(80))           # 真实姓名
    id_card = db.Column(db.String(18))             # 身份证号
    phone = db.Column(db.String(20))               # 手机号
    is_verified = db.Column(db.Boolean, default=False)  # 是否验证
    bio = db.Column(db.Text)                       # 个人简介
    
    def set_password(self, password):
        """设置密码的哈希值"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def get_avatar_url(self):
        """获取用户头像的完整URL"""
        if self.avatar == 'default.jpg':
            # 默认头像
            return '/static/images/default.jpg'
        else:
            # 用户自定义头像（保存在uploads/avatars目录下）
            return f'/static/uploads/avatars/{self.avatar}'

class Artist(db.Model):
    """艺术家表"""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    birth_year = db.Column(db.Integer)
    death_year = db.Column(db.Integer)
    country = db.Column(db.String(50))
    biography = db.Column(db.Text)
    era = db.Column(db.String(50))
    influence = db.Column(db.Text)

class Artwork(db.Model):
    """艺术作品表"""
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    artist_id = db.Column(db.Integer, db.ForeignKey('artist.id'))
    year = db.Column(db.Integer)
    style = db.Column(db.String(100))
    medium = db.Column(db.String(100))
    dimensions = db.Column(db.String(100))
    location = db.Column(db.String(200))
    description = db.Column(db.Text)
    art_value = db.Column(db.Text)
    historical_context = db.Column(db.Text)
    creation_story = db.Column(db.Text)
    image_url = db.Column(db.String(300))
    source = db.Column(db.String(200))
    submitted_by = db.Column(db.Integer, db.ForeignKey('user.id'))
    is_approved = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)
    artist = db.relationship('Artist', backref='artworks')

class Feedback(db.Model):
    """用户反馈表"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    feedback_type = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    contact_info = db.Column(db.String(100))
    created_at = db.Column(db.DateTime, default=datetime.now)
    is_read = db.Column(db.Boolean, default=False)
    user = db.relationship('User', backref='feedbacks')

# ========== 5. 创建数据库表 ==========
def init_database():
    """初始化数据库"""
    with app.app_context():
        # 创建所有表
        db.create_all()
        print("✅ 数据库表创建完成！")
        
        # 检查是否有数据，如果没有则添加示例数据
        if Artist.query.count() == 0:
            print("添加示例艺术家数据...")
            try:
                # 添加示例艺术家
                artists = [
                    Artist(
                        name="文森特·梵高",
                        birth_year=1853,
                        death_year=1890,
                        country="荷兰",
                        biography="后印象派画家，以其独特的色彩和笔触闻名。",
                        era="后印象派",
                        influence="对20世纪艺术有深远影响"
                    ),
                    Artist(
                        name="列奥纳多·达·芬奇",
                        birth_year=1452,
                        death_year=1519,
                        country="意大利",
                        biography="文艺复兴时期的全才，画家、雕塑家、建筑师、科学家。",
                        era="文艺复兴",
                        influence="文艺复兴艺术的代表人物"
                    ),
                    Artist(
                        name="毕加索",
                        birth_year=1881,
                        death_year=1973,
                        country="西班牙",
                        biography="现代艺术的重要人物，立体主义的创始人之一。",
                        era="现代艺术",
                        influence="20世纪艺术革命的关键人物"
                    )
                ]
                
                for artist in artists:
                    db.session.add(artist)
                
                db.session.commit()
                print(f"✅ 已添加 {len(artists)} 位艺术家")
                
                # 添加示例作品
                if Artwork.query.count() == 0:
                    artworks = [
                        Artwork(
                            title="星夜",
                            artist_id=1,  # 梵高
                            year=1889,
                            style="后印象派",
                            medium="油画",
                            dimensions="73.7 × 92.1 cm",
                            location="纽约现代艺术博物馆",
                            description="梵高在圣雷米精神病院期间创作的代表作。",
                            image_url="/static/images/starry_night.jpg",
                            is_approved=True
                        ),
                        Artwork(
                            title="蒙娜丽莎",
                            artist_id=2,  # 达·芬奇
                            year=1503,
                            style="文艺复兴",
                            medium="油画",
                            dimensions="77 × 53 cm",
                            location="巴黎卢浮宫",
                            description="世界上最著名的肖像画之一。",
                            image_url="/static/images/mona_lisa.jpg",
                            is_approved=True
                        ),
                        Artwork(
                            title="格尔尼卡",
                            artist_id=3,  # 毕加索
                            year=1937,
                            style="立体主义",
                            medium="油画",
                            dimensions="349.3 × 776.6 cm",
                            location="马德里索菲亚王后国家艺术中心博物馆",
                            description="抗议西班牙内战中格尔尼卡轰炸的作品。",
                            image_url="https://upload.wikimedia.org/wikipedia/en/thumb/7/74/PicassoGuernica.jpg/800px-PicassoGuernica.jpg",
                            is_approved=True
                        )
                    ]
                    
                    for artwork in artworks:
                        db.session.add(artwork)
                    
                    db.session.commit()
                    print(f"✅ 已添加 {len(artworks)} 件作品")
                
            except Exception as e:
                print(f"⚠️ 添加示例数据时出错：{e}")
        
        # 添加一个演示用户
        if User.query.count() == 0:
            try:
                demo_user = User(
                    username='demo',
                    email='demo@example.com',
                    avatar='default.jpg'
                )
                demo_user.set_password('demo123')
                db.session.add(demo_user)
                db.session.commit()
                print("✅ 演示用户创建成功：用户名 demo，密码 demo123")
            except Exception as e:
                print(f"⚠️ 创建演示用户时出错：{e}")

# ========== 6. 主页面路由 ==========
@app.route('/')
def index():
    """网站首页"""
    # 获取最新的12件作品用于首页展示
    latest_artworks = Artwork.query.filter_by(is_approved=True).order_by(Artwork.created_at.desc()).limit(12).all()
    user_logged_in = session.get('user_id') is not None
    return render_template('index.html', 
                          latest_artworks=latest_artworks, 
                          user_logged_in=user_logged_in)

# ========== 7. 作品相关路由 ==========
@app.route('/artworks')
def artworks():
    """作品列表页 - 支持风格、时代、艺术家筛选及视图模式"""
    # 获取筛选参数
    style = request.args.get('style', '')
    era = request.args.get('era', '')
    artist_name = request.args.get('artist', '')
    view_mode = request.args.get('view', 'grid')  # 视图模式，默认网格

    # 构建基础查询（只显示已审核作品）
    query = Artwork.query.filter_by(is_approved=True)

    # 按风格筛选
    if style:
        query = query.filter_by(style=style)

    # 按时代筛选（假设 era 对应 Artist.era 字段）
    if era:
        query = query.join(Artist).filter(Artist.era == era)

    # 按艺术家姓名筛选
    if artist_name:
        query = query.join(Artist).filter(Artist.name == artist_name)

    # 执行查询
    artworks_list = query.all()

    # 获取所有艺术家列表（用于前端下拉框动态加载）
    all_artists = Artist.query.order_by(Artist.name).all()

    user_logged_in = session.get('user_id') is not None

    return render_template('artwork_list.html',
                           artworks=artworks_list,
                           all_artists=all_artists,
                           user_logged_in=user_logged_in,
                           current_style=style,
                           current_era=era,
                           current_artist=artist_name,
                           view_mode=view_mode)

@app.route('/artwork/<int:artwork_id>')
def artwork_detail(artwork_id):
    """作品详情页"""
    artwork = Artwork.query.get_or_404(artwork_id)
    user_logged_in = session.get('user_id') is not None
    return render_template('artwork_detail.html', artwork=artwork, user_logged_in=user_logged_in)

# ========== 8. 作者相关路由 ==========
@app.route('/authors')
def authors():
    """作者列表页"""
    authors_list = Artist.query.all()
    user_logged_in = session.get('user_id') is not None
    return render_template('author_list.html', authors=authors_list, user_logged_in=user_logged_in)

@app.route('/author/<int:author_id>')
def author_detail(author_id):
    """作者详情页"""
    author = Artist.query.get_or_404(author_id)
    author_artworks = Artwork.query.filter_by(artist_id=author_id, is_approved=True).all()
    user_logged_in = session.get('user_id') is not None
    return render_template('author_detail.html', author=author, artworks=author_artworks, user_logged_in=user_logged_in)

# ========== 9. 用户相关路由 ==========
@app.route('/login', methods=['GET', 'POST'])
def login():
    """登录页面"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        
        if not username or not password:
            flash('请输入用户名和密码！', 'error')
            return render_template('login.html')
        
        try:
            # 查找用户（支持用户名或邮箱登录）
            user = User.query.filter(
                (User.username == username) | (User.email == username)
            ).first()
            
            if user and user.check_password(password):
                # 登录成功
                session['user_id'] = user.id
                session['username'] = user.username
                session['is_reviewer'] = user.is_reviewer
                session['avatar'] = user.avatar
                
                flash(f'欢迎回来，{user.username}！', 'success')
                return redirect(url_for('index'))
            else:
                flash('用户名或密码错误！', 'error')
                return render_template('login.html')
                
        except Exception as e:
            print(f"登录错误详情: {e}")
            flash('登录失败，请检查用户名和密码。', 'error')
            return render_template('login.html')
    
    return render_template('login.html')

@app.route('/user/real-name-auth', methods=['GET', 'POST'])
def real_name_auth():
    """实名认证页面"""
    user_id = session.get('user_id')
    if not user_id:
        flash('请先登录。', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(user_id)
    if not user:
        flash('用户不存在，请重新登录。', 'error')
        session.clear()
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        real_name = request.form.get('real_name', '').strip()
        id_card = request.form.get('id_card', '').strip()
        phone = request.form.get('phone', '').strip()
        
        # 验证表单数据
        errors = []
        if not real_name:
            errors.append('请输入真实姓名')
        if not id_card or len(id_card) != 18:
            errors.append('请输入有效的18位身份证号码')
        if not phone or len(phone) != 11:
            errors.append('请输入有效的11位手机号码')
        
        if errors:
            for error in errors:
                flash(error, 'error')
        else:
            # 保存认证信息
            user.real_name = real_name
            user.id_card = id_card
            user.phone = phone
            user.is_verified = True
            
            db.session.commit()
            
            flash('实名认证已成功！', 'success')
            return redirect(url_for('user_center'))
    
    user_logged_in = True
    return render_template('real_name_auth.html', 
                          user_logged_in=user_logged_in,
                          user=user,
                          current_user=user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """注册页面"""
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        
        # 验证输入
        errors = []
        if not username or len(username) < 3:
            errors.append('用户名至少需要3个字符！')
        if not email or '@' not in email:
            errors.append('请输入有效的邮箱地址！')
        if not password or len(password) < 6:
            errors.append('密码至少需要6个字符！')
        if password != confirm_password:
            errors.append('两次输入的密码不一致！')
        
        if errors:
            for error in errors:
                flash(error, 'error')
            return render_template('register.html')
        
        try:
            # 详细检查用户名和邮箱是否已存在
            existing_username = User.query.filter_by(username=username).first()
            existing_email = User.query.filter_by(email=email).first()
            
            if existing_username:
                flash('该用户名已被注册！', 'error')
                return render_template('register.html')
            
            if existing_email:
                flash('该邮箱已被注册！', 'error')
                return render_template('register.html')
            
            # 创建新用户
            new_user = User(username=username, email=email)
            new_user.set_password(password)
            
            db.session.add(new_user)
            db.session.commit()
            
            # 自动登录
            session['user_id'] = new_user.id
            session['username'] = new_user.username
            session['is_reviewer'] = new_user.is_reviewer
            session['avatar'] = new_user.avatar
            
            flash(f'注册成功！欢迎加入艺术世界，{username}！', 'success')
            return redirect(url_for('index'))
            
        except Exception as e:
            db.session.rollback()
            print(f"注册错误详情: {e}")
            flash('注册失败，请稍后再试。', 'error')
            return render_template('register.html')
    
    return render_template('register.html')

# ========== 修复后的user_center路由 ==========
@app.route('/user')
def user_center():
    """个人中心页面"""
    user_id = session.get('user_id')
    if not user_id:
        flash('请先登录。', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(user_id)
    if not user:
        flash('用户不存在，请重新登录。', 'error')
        session.clear()
        return redirect(url_for('login'))
    
    # 计算统计数据
    from datetime import date
    
    # 今日开始时间
    today = date.today()
    today_start = datetime(today.year, today.month, today.day)
    
    # 获取当前用户的所有投稿
    submissions = Artwork.query.filter_by(submitted_by=user_id).all()
    submission_count = len(submissions)
    approved_count = len([s for s in submissions if s.is_approved])
    pending_submission_count = len([s for s in submissions if not s.is_approved])
    
    # 今日新增（用户今日投稿的作品数量）
    today_submissions = Artwork.query.filter(
        Artwork.submitted_by == user_id,
        Artwork.created_at >= today_start
    ).all()
    today_new_count = len(today_submissions)
    
    # 获取待审作品数量（仅审核员可见）
    pending_count = 0
    total_approved_count = 0
    total_today_new_count = 0
    
    if user.is_reviewer:
        # 所有待审作品
        pending_count = Artwork.query.filter_by(is_approved=False).count()
        
        # 所有已审核作品
        total_approved_count = Artwork.query.filter_by(is_approved=True).count()
        
        # 今日新增的所有作品（所有用户）
        total_today_new_count = Artwork.query.filter(
            Artwork.created_at >= today_start
        ).count()
    
    # 搜索次数（这里简化为固定值，实际应从数据库获取）
    search_count = 0
    
    # 计算头像URL
    avatar_url = user.get_avatar_url()
    
    # 修复：传递所有需要的变量
    return render_template('user_center.html', 
                          user=user,
                          current_user=user,
                          user_logged_in=True,
                          avatar_url=avatar_url,
                          submission_count=submission_count,
                          approved_count=approved_count,
                          pending_submission_count=pending_submission_count,
                          today_new_count=today_new_count,  # 用户今日新增
                          pending_count=pending_count,
                          total_approved_count=total_approved_count,  # 所有已审核作品
                          total_today_new_count=total_today_new_count,  # 所有今日新增
                          search_count=search_count)

@app.route('/my_submissions')
def my_submissions():
    """我的投稿页面"""
    user_id = session.get('user_id')
    if not user_id:
        flash('请先登录。', 'warning')
        return redirect(url_for('login'))
    
    # 获取URL参数中的消息
    message = request.args.get('message', '')
    message_type = request.args.get('message_type', '')
    
    # 清除所有flash消息，避免重复
    session.pop('_flashes', None)
    
    # 获取当前用户的所有投稿
    submissions = Artwork.query.filter_by(submitted_by=user_id).all()
    
    # 为每件作品添加艺术家信息（如果需要）
    for submission in submissions:
        if submission.artist_id:
            submission.artist_info = Artist.query.get(submission.artist_id)
        else:
            submission.artist_info = None
    
    # 统计信息
    total = len(submissions)
    approved = len([s for s in submissions if s.is_approved])
    pending = len([s for s in submissions if not s.is_approved])
    
    user = User.query.get(user_id)
    return render_template('my_submissions.html', 
                          user=user,
                          current_user=user,
                          user_logged_in=True,
                          submissions=submissions,
                          total=total,
                          approved=approved,
                          pending=pending,
                          message=message,
                          message_type=message_type)

@app.route('/submit-artwork', methods=['GET', 'POST'])
def submit_artwork():
    """投稿作品页面"""
    user_id = session.get('user_id')
    if not user_id:
        flash('请先登录才能投稿。', 'warning')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        # 获取表单数据
        title = request.form.get('title', '').strip()
        artist_name = request.form.get('artist', '').strip()
        year = request.form.get('year', '').strip()
        style = request.form.get('style', '').strip()
        description = request.form.get('description', '').strip()
        image_url = request.form.get('image_url', '').strip()
        
        # 验证必填字段
        if not title or not artist_name:
            flash('作品标题和作者是必填项！', 'error')
            return render_template('submit_artwork.html', user_logged_in=True)
        
        try:
            # 查找或创建艺术家
            artist = Artist.query.filter_by(name=artist_name).first()
            if not artist:
                artist = Artist(
                    name=artist_name,
                    country="未知",
                    biography=f"艺术家：{artist_name}"
                )
                db.session.add(artist)
                db.session.commit()
                print(f"创建了新艺术家：{artist_name}")
            
            # 创建作品记录
            artwork = Artwork(
                title=title,
                artist_id=artist.id,
                year=year if year else None,
                style=style,
                description=description,
                image_url=image_url if image_url else '/static/images/default.jpg',
                submitted_by=user_id,
                is_approved=False  # 新投稿默认为未审核
            )
            
            db.session.add(artwork)
            db.session.commit()
            
            print(f"用户 {user_id} 投稿了作品：{title}")
            
            # 使用URL参数传递消息，不通过flash系统
            return redirect(url_for('my_submissions', message='作品投稿已提交，等待审核！', message_type='success'))
            
        except Exception as e:
            db.session.rollback()
            print(f"投稿错误: {e}")
            return redirect(url_for('my_submissions', message='投稿过程中出现错误，请稍后再试。', message_type='error'))
    
    # 处理GET请求时可能的消息
    message = request.args.get('message', '')
    message_type = request.args.get('message_type', '')
    
    user_logged_in = True
    user = User.query.get(user_id) if user_id else None
    return render_template('submit_artwork.html', 
                          user=user,
                          current_user=user,
                          user_logged_in=user_logged_in,
                          message=message,
                          message_type=message_type)

@app.route('/user/feedback', methods=['GET', 'POST'])
def user_feedback():
    """用户反馈页面"""
    user_id = session.get('user_id')
    if not user_id:
        flash('请先登录才能提交反馈。', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(user_id)
    if not user:
        flash('用户不存在，请重新登录。', 'error')
        session.clear()
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        feedback_type = request.form.get('feedback_type', '').strip()
        content = request.form.get('content', '').strip()
        contact_info = request.form.get('contact_info', '').strip()
        
        if not feedback_type:
            flash('请选择反馈类型！', 'error')
            return render_template('user_feedback.html', 
                                 user=user,
                                 current_user=user,
                                 user_logged_in=True)
        
        if not content or len(content) < 10:
            flash('反馈内容至少需要10个字符！', 'error')
            return render_template('user_feedback.html', 
                                 user=user,
                                 current_user=user,
                                 user_logged_in=True)
        
        try:
            feedback = Feedback(
                user_id=session['user_id'],
                feedback_type=feedback_type,
                content=content,
                contact_info=contact_info if contact_info else None
            )
            
            db.session.add(feedback)
            db.session.commit()
            
            flash('您的反馈已成功提交！感谢您的宝贵意见。', 'success')
            return redirect(url_for('user_feedback'))
            
        except Exception as e:
            db.session.rollback()
            print(f"反馈提交错误: {e}")
            flash('提交反馈时出现错误，请稍后再试。', 'error')
            return render_template('user_feedback.html', 
                                 user=user,
                                 current_user=user,
                                 user_logged_in=True)
    
    return render_template('user_feedback.html', 
                          user=user,
                          current_user=user,
                          user_logged_in=True)

@app.route('/logout')
def logout():
    """退出登录"""
    session.clear()
    flash('您已成功退出。', 'success')
    return redirect(url_for('index'))

# ========== 修复用户个人资料相关路由 ==========
@app.route('/user/profile', methods=['GET', 'POST'])
def user_profile():
    """编辑个人资料页面"""
    user_id = session.get('user_id')
    if not user_id:
        flash('请先登录。', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(user_id)
    if not user:
        flash('用户不存在，请重新登录。', 'error')
        return redirect(url_for('login'))
    
    if request.method == 'POST':
        try:
            # 获取表单数据
            email = request.form.get('email', '').strip()
            real_name = request.form.get('real_name', '').strip()
            phone = request.form.get('phone', '').strip()
            bio = request.form.get('bio', '').strip()
            
            # 验证邮箱是否已存在（除了当前用户）
            if email != user.email:
                existing_email = User.query.filter_by(email=email).first()
                if existing_email:
                    flash('该邮箱已被其他用户使用！', 'error')
                    return redirect(url_for('user_profile'))
            
            # 更新基本信息
            user.email = email
            user.real_name = real_name
            user.phone = phone
            user.bio = bio
            
            # 处理头像上传
            if 'avatar' in request.files:
                avatar_file = request.files['avatar']
                if avatar_file and avatar_file.filename != '':
                    # 检查文件类型
                    allowed_extensions = {'jpg', 'jpeg', 'png', 'gif'}
                    filename = avatar_file.filename
                    file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
                    
                    if file_ext not in allowed_extensions:
                        flash('只支持 JPG, PNG, GIF 格式的图片！', 'error')
                        return redirect(url_for('user_profile'))
                    
                    # 检查文件大小
                    avatar_file.seek(0, os.SEEK_END)
                    file_size = avatar_file.tell()
                    avatar_file.seek(0)
                    
                    if file_size > 5 * 1024 * 1024:  # 5MB
                        flash('头像文件大小不能超过5MB！', 'error')
                        return redirect(url_for('user_profile'))
                    
                    # 生成安全的文件名
                    timestamp = str(int(time.time()))
                    hash_str = hashlib.md5((str(user.id) + timestamp).encode()).hexdigest()[:8]
                    new_filename = f"avatar_{user.id}_{hash_str}.{file_ext}"
                    
                    # 创建保存目录
                    avatar_dir = os.path.join('static', 'uploads', 'avatars')
                    os.makedirs(avatar_dir, exist_ok=True)
                    
                    # 保存文件
                    avatar_path = os.path.join(avatar_dir, new_filename)
                    
                    try:
                        avatar_file.save(avatar_path)
                        # 更新用户头像字段
                        user.avatar = new_filename
                        # 更新session中的头像信息
                        session['avatar'] = new_filename
                        flash('头像更新成功！', 'success')
                    except Exception as e:
                        print(f"保存头像文件错误: {e}")
                        flash('头像保存失败，请重试。', 'error')
                        return redirect(url_for('user_profile'))
            
            # 提交到数据库
            db.session.commit()
            flash('个人资料更新成功！', 'success')
            return redirect(url_for('user_profile'))
            
        except Exception as e:
            db.session.rollback()
            print(f"更新个人资料错误: {e}")
            flash('更新失败，请稍后再试。', 'error')
            return redirect(url_for('user_profile'))
    
    # GET请求：显示编辑页面
    # 计算头像URL
    avatar_url = user.get_avatar_url()
    
    return render_template('user_profile.html', 
                         user=user,
                         current_user=user, 
                         user_logged_in=True,
                         avatar_url=avatar_url)

# ========== 审核相关路由 ==========
@app.route('/review/pending')
def review_pending():
    """审核员查看待审作品"""
    user_id = session.get('user_id')
    if not user_id:
        flash('请先登录。', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(user_id)
    if not user:
        flash('用户不存在，请重新登录。', 'error')
        session.clear()
        return redirect(url_for('login'))
    
    # 检查是否是审核员
    if not user.is_reviewer:
        flash('需要审核员权限才能访问此页面。', 'error')
        return redirect(url_for('user_center'))
    
    # 获取待审作品 - 修复查询逻辑
    # 查询所有未审核的作品，包括审核员自己投稿的
    pending_artworks = Artwork.query.filter_by(is_approved=False)\
        .order_by(Artwork.created_at.desc())\
        .all()
    
    # 预加载投稿人信息
    artworks_data = []
    for artwork in pending_artworks:
        # 获取投稿人信息
        submitter = User.query.get(artwork.submitted_by) if artwork.submitted_by else None
        
        artworks_data.append({
            'id': artwork.id,
            'title': artwork.title,
            'artist': artwork.artist,
            'year': artwork.year,
            'submitted_by': artwork.submitted_by,
            'submitter_name': submitter.username if submitter else "未知用户",
            'submitter_username': submitter.username if submitter else "未知用户",
            'created_at': artwork.created_at,
            'source': artwork.source,
            'image_url': artwork.image_url,
            'style': artwork.style,
            'medium': artwork.medium,
            'dimensions': artwork.dimensions,
            'location': artwork.location,
            'description': artwork.description,
        })
    
    # 修复：传递所有需要的变量，使用正确的变量名
    return render_template('review_pending.html', 
                          user=user,
                          current_user=user,
                          user_logged_in=True,
                          artworks=artworks_data,  # 使用artworks而不是pending_artworks
                          pending_count=len(artworks_data))

@app.route('/apply-reviewer', methods=['GET', 'POST'])
def apply_reviewer():
    """申请成为审核员"""
    user_id = session.get('user_id')
    if not user_id:
        flash('请先登录。', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(user_id)
    if not user:
        flash('用户不存在，请重新登录。', 'error')
        session.clear()
        return redirect(url_for('login'))
    
    if user.is_reviewer:
        flash('您已经是审核员了！', 'info')
        return redirect(url_for('user_center'))
    
    if request.method == 'POST':
        application_reason = request.form.get('reason', '').strip()
        
        if not application_reason:
            flash('请填写申请理由。', 'error')
            return render_template('apply_reviewer.html',
                                 user=user,
                                 current_user=user,
                                 user_logged_in=True)
        
        # 直接批准（简化版）
        user.is_reviewer = True
        db.session.commit()
        
        # 更新session中的用户信息
        session['is_reviewer'] = True
        
        flash('恭喜！您已成为审核员。', 'success')
        return redirect(url_for('user_center'))
    
    return render_template('apply_reviewer.html',
                         user=user,
                         current_user=user,
                         user_logged_in=True)

# ========== 其他功能路由 ==========
@app.route('/change_password', methods=['POST'])
def change_password():
    """修改密码"""
    user_id = session.get('user_id')
    if not user_id:
        flash('请先登录。', 'warning')
        return redirect(url_for('login'))
    
    user = User.query.get(user_id)
    if not user:
        flash('用户不存在，请重新登录。', 'error')
        session.clear()
        return redirect(url_for('login'))
    
    current_password = request.form.get('current_password', '')
    new_password = request.form.get('new_password', '')
    confirm_password = request.form.get('confirm_new_password', '')
    
    # 验证输入
    if not current_password or not new_password or not confirm_password:
        flash('请填写所有密码字段！', 'error')
        return redirect(url_for('user_center'))
    
    if new_password != confirm_password:
        flash('新密码与确认密码不一致！', 'error')
        return redirect(url_for('user_center'))
    
    if len(new_password) < 6:
        flash('新密码至少需要6个字符！', 'error')
        return redirect(url_for('user_center'))
    
    # 验证当前密码
    if not user.check_password(current_password):
        flash('当前密码错误！', 'error')
        return redirect(url_for('user_center'))
    
    # 更新密码
    try:
        user.set_password(new_password)
        db.session.commit()
        flash('密码修改成功！', 'success')
    except Exception as e:
        db.session.rollback()
        print(f"修改密码错误: {e}")
        flash('修改密码时出现错误，请稍后再试。', 'error')
    
    return redirect(url_for('user_center'))

# ========== 10. AI搜索功能 ==========
@app.route('/api/ai-search', methods=['POST'])
def ai_search():
    """处理首页的AI搜索提问"""
    data = request.get_json()
    question = data.get('question', '').strip()

    if not question:
        return jsonify({'error': '问题不能为空'}), 400

    try:
        response = client.chat.completions.create(
            model="deepseek-v3.2",
            messages=[
                {
                    "role": "system",
                    "content": "你是一位专业、热情的艺术史学者和博物馆讲解员。请用清晰、准确、生动且易于理解的中文回答用户关于艺术家、艺术作品、艺术流派、艺术史的所有问题。如果遇到不确定的信息，请诚实说明。回答请控制在三段以内。"
                },
                {
                    "role": "user",
                    "content": question
                }
            ],
            max_tokens=800,
            temperature=0.7,
        )
        ai_answer = response.choices[0].message.content

        return jsonify({
            'answer': ai_answer,
            'suggestions': []
        })

    except Exception as e:
        print(f"AI API 调用错误: {e}")
        backup_answer = f"您好！您的问题是：'{question}'。目前AI深度解读服务正在连接中，请稍后再试。\n\n您也可以直接浏览我们的'作品'或'作者'页面，获取丰富的艺术资料。"
        return jsonify({
            'answer': backup_answer,
            'suggestions': ['文艺复兴', '印象派', '现代艺术', '中国水墨画']
        })

# ========== 11. 辅助接口 ==========
@app.route('/api/latest-artworks')
def api_latest_artworks():
    """为首页提供最新作品的JSON数据"""
    artworks = Artwork.query.filter_by(is_approved=True).order_by(Artwork.created_at.desc()).limit(8).all()
    result = []
    for art in artworks:
        result.append({
            'id': art.id,
            'title': art.title,
            'artist_name': art.artist.name if art.artist else '未知艺术家',
            'image_url': art.image_url if art.image_url else '/static/images/default.jpg',
            'year': art.year
        })
    return jsonify(result)

@app.route('/admin/create-test-user')
def create_test_user():
    """创建测试用户"""
    try:
        # 检查是否已存在测试用户
        test_user = User.query.filter_by(username='testuser').first()
        if not test_user:
            test_user = User(
                username='testuser',
                email='test@example.com'
            )
            test_user.set_password('test123')
            db.session.add(test_user)
            db.session.commit()
            
            # 自动登录
            session['user_id'] = test_user.id
            session['username'] = test_user.username
            session['is_reviewer'] = test_user.is_reviewer
            session['avatar'] = test_user.avatar
            
            return '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>测试用户创建成功</title>
                <style>
                    body { font-family: Arial, sans-serif; padding: 40px; text-align: center; }
                    .success { color: green; font-size: 24px; margin-bottom: 20px; }
                    .info { background: #f0f8ff; padding: 20px; border-radius: 10px; margin: 20px auto; max-width: 500px; }
                    .btn { display: inline-block; padding: 10px 20px; background: #4a90e2; color: white; text-decoration: none; border-radius: 5px; margin: 10px; }
                </style>
            </head>
            <body>
                <div class="success">✅ 测试用户创建成功！</div>
                <div class="info">
                    <p><strong>用户名：</strong>testuser</p>
                    <p><strong>密码：</strong>test123</p>
                    <p><strong>邮箱：</strong>test@example.com</p>
                    <p><strong>状态：</strong>已自动登录</p>
                </div>
                <a href="/" class="btn">返回首页</a>
                <a href="/user" class="btn">进入个人中心</a>
            </body>
            </html>
            '''
        else:
            return '''
            <!DOCTYPE html>
            <html>
            <head>
                <title>测试用户已存在</title>
                <style>
                    body { font-family: Arial, sans-serif; padding: 40px; text-align: center; }
                    .info { background: #fff8e1; padding: 20px; border-radius: 10px; margin: 20px auto; max-width: 500px; }
                    .btn { display: inline-block; padding: 10px 20px; background: #4a90e2; color: white; text-decoration: none; border-radius: 5px; margin: 10px; }
                </style>
            </head>
            <body>
                <div class="info">
                    <p><strong>测试用户已存在</strong></p>
                    <p>用户名：testuser</p>
                    <p>密码：test123</p>
                    <p>您可以直接使用这些凭据登录。</p>
                </div>
                <a href="/" class="btn">返回首页</a>
                <a href="/login" class="btn">前往登录</a>
            </body>
            </html>
            '''
    except Exception as e:
        return f'''
        <!DOCTYPE html>
        <html>
        <head>
            <title>错误</title>
            <style>
                body {{ font-family: Arial, sans-serif; padding: 40px; text-align: center; }}
                .error {{ color: red; font-size: 18px; }}
            </style>
        </head>
        <body>
            <div class="error">❌ 创建测试用户时出错：{str(e)}</div>
            <a href="/">返回首页</a>
        </body>
        </html>
        '''
    
@app.route('/api/artwork/<int:artwork_id>/approve', methods=['POST'])
def approve_artwork(artwork_id):
    """通过作品审核"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    user = User.query.get(user_id)
    if not user or not user.is_reviewer:
        return jsonify({'success': False, 'message': '需要审核员权限'}), 403
    
    artwork = Artwork.query.get(artwork_id)
    if not artwork:
        return jsonify({'success': False, 'message': '作品不存在'}), 404
    
    try:
        artwork.is_approved = True
        db.session.commit()
        
        # 重新计算审核后的统计数据
        from datetime import date
        today = date.today()
        today_start = datetime(today.year, today.month, today.day)
        
        # 待审作品数量
        pending_count = Artwork.query.filter_by(is_approved=False).count()
        
        # 已审核作品总数
        approved_count = Artwork.query.filter_by(is_approved=True).count()
        
        # 今日新增作品数（所有用户）
        today_new_count = Artwork.query.filter(
            Artwork.created_at >= today_start
        ).count()
        
        return jsonify({
            'success': True, 
            'message': '审核通过',
            'stats': {
                'pending_count': pending_count,
                'approved_count': approved_count,
                'today_new_count': today_new_count
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/artwork/<int:artwork_id>/reject', methods=['POST'])
def reject_artwork(artwork_id):
    """拒绝作品审核"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    user = User.query.get(user_id)
    if not user or not user.is_reviewer:
        return jsonify({'success': False, 'message': '需要审核员权限'}), 403
    
    artwork = Artwork.query.get(artwork_id)
    if not artwork:
        return jsonify({'success': False, 'message': '作品不存在'}), 404
    
    try:
        # 在实际应用中，这里可以添加拒绝理由，并通知用户
        db.session.delete(artwork)  # 删除作品
        db.session.commit()
        
        # 重新计算审核后的统计数据
        from datetime import date
        today = date.today()
        today_start = datetime(today.year, today.month, today.day)
        
        # 待审作品数量
        pending_count = Artwork.query.filter_by(is_approved=False).count()
        
        # 已审核作品总数
        approved_count = Artwork.query.filter_by(is_approved=True).count()
        
        # 今日新增作品数（所有用户）
        today_new_count = Artwork.query.filter(
            Artwork.created_at >= today_start
        ).count()
        
        return jsonify({
            'success': True, 
            'message': '作品已拒绝',
            'stats': {
                'pending_count': pending_count,
                'approved_count': approved_count,
                'today_new_count': today_new_count
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    
# ========== 撤回和删除功能 ==========
@app.route('/api/artwork/<int:artwork_id>/withdraw', methods=['POST'])
def withdraw_artwork(artwork_id):
    """撤回作品（投稿者使用）"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404
    
    artwork = Artwork.query.get(artwork_id)
    if not artwork:
        return jsonify({'success': False, 'message': '作品不存在'}), 404
    
    # 检查权限：只有投稿者本人可以撤回
    if artwork.submitted_by != user.id and not user.is_reviewer:
        return jsonify({'success': False, 'message': '只能撤回自己的作品'}), 403
    
    # 检查状态：只能撤回未审核的作品
    if artwork.is_approved:
        return jsonify({'success': False, 'message': '已审核的作品不能撤回，请联系管理员'}), 400
    
    try:
        db.session.delete(artwork)
        db.session.commit()
        return jsonify({
            'success': True, 
            'message': '作品已成功撤回',
            'redirect_url': url_for('my_submissions')
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/artwork/<int:artwork_id>/delete', methods=['POST'])
def delete_artwork(artwork_id):
    """删除作品（投稿者或审核员使用）"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404
    
    artwork = Artwork.query.get(artwork_id)
    if not artwork:
        return jsonify({'success': False, 'message': '作品不存在'}), 404
    
    # 检查权限：投稿者只能删除自己的作品，审核员可以删除任何作品
    if artwork.submitted_by != user.id and not user.is_reviewer:
        return jsonify({'success': False, 'message': '没有权限删除此作品'}), 403
    
    try:
        db.session.delete(artwork)
        db.session.commit()
        
        # 如果是审核员在审核页面删除作品，可能需要更新统计
        from datetime import date
        today = date.today()
        today_start = datetime(today.year, today.month, today.day)
        
        # 待审作品数量
        pending_count = Artwork.query.filter_by(is_approved=False).count()
        
        # 已审核作品总数
        approved_count = Artwork.query.filter_by(is_approved=True).count()
        
        # 今日新增作品数（所有用户）
        today_new_count = Artwork.query.filter(
            Artwork.created_at >= today_start
        ).count()
        
        return jsonify({
            'success': True, 
            'message': '作品已删除',
            'stats': {
                'pending_count': pending_count,
                'approved_count': approved_count,
                'today_new_count': today_new_count
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    
@app.route('/api/stats')
def get_stats():
    """获取统计数字"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    user = User.query.get(user_id)
    if not user:
        return jsonify({'success': False, 'message': '用户不存在'}), 404
    
    from datetime import date
    today = date.today()
    today_start = datetime(today.year, today.month, today.day)
    
    # 待审作品数量
    pending_count = Artwork.query.filter_by(is_approved=False).count()
    
    # 已审核作品总数
    approved_count = Artwork.query.filter_by(is_approved=True).count()
    
    # 今日新增作品数（所有用户）
    today_new_count = Artwork.query.filter(
        Artwork.created_at >= today_start
    ).count()
    
    return jsonify({
        'success': True,
        'stats': {
            'pending_count': pending_count,
            'approved_count': approved_count,
            'today_new_count': today_new_count
        }
    })

@app.route('/api/batch-approve', methods=['POST'])
def batch_approve():
    """批量通过作品审核"""
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': '请先登录'}), 401
    
    user = User.query.get(user_id)
    if not user or not user.is_reviewer:
        return jsonify({'success': False, 'message': '需要审核员权限'}), 403
    
    data = request.get_json()
    artwork_ids = data.get('artwork_ids', [])
    
    if not artwork_ids:
        return jsonify({'success': False, 'message': '没有选择作品'}), 400
    
    try:
        # 批量更新作品状态
        Artwork.query.filter(Artwork.id.in_(artwork_ids)).update(
            {Artwork.is_approved: True}, 
            synchronize_session=False
        )
        db.session.commit()
        
        # 重新计算统计数字
        from datetime import date
        today = date.today()
        today_start = datetime(today.year, today.month, today.day)
        
        pending_count = Artwork.query.filter_by(is_approved=False).count()
        approved_count = Artwork.query.filter_by(is_approved=True).count()
        today_new_count = Artwork.query.filter(
            Artwork.created_at >= today_start
        ).count()
        
        return jsonify({
            'success': True, 
            'message': f'已批量通过 {len(artwork_ids)} 件作品',
            'stats': {
                'pending_count': pending_count,
                'approved_count': approved_count,
                'today_new_count': today_new_count
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500

# ========== 12. 应用启动 ==========
if __name__ == '__main__':
    # 初始化数据库
    init_database()
    
    # 运行Flask开发服务器
    print("=" * 50)
    print("🎨 艺术与世界网站启动成功！")
    print("🌐 请访问：http://localhost:5000")
    print("🔑 快速登录：访问 http://localhost:5000/admin/create-test-user")
    print("👤 演示用户：用户名 demo，密码 demo123")
    print("=" * 50)
    
    app.run(debug=True, port=5000)