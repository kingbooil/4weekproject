from flask import Flask, render_template, request, redirect, url_for, session, send_file
import pymysql
import os

app = Flask(__name__)

app.secret_key = '1234'

UPLOAD_FOLDER = 'uploads'

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

PROFILE_UPLOAD_FOLDER = 'profile_images'
if not os.path.exists(PROFILE_UPLOAD_FOLDER):
    os.makedirs(PROFILE_UPLOAD_FOLDER)


app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


conn = pymysql.connect(host='localhost', port=3306, user='root', passwd='1234', charset='utf8')

cursor = conn.cursor()

cursor.execute("DROP DATABASE notice;") 
cursor.execute("CREATE DATABASE notice;")
cursor.execute("USE notice;")

cursor.execute("""
        CREATE TABLE board (
            `board_id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY, 
               `title` VARCHAR(50)      NOT NULL,  
               `content`     VARCHAR(1000)    NOT NULL, 
               `secret` VARCHAR(50), 
               `secret_password` VARCHAR(50)
               );""")
cursor.execute("""
        CREATE TABLE login (
            `nick`     VARCHAR(50)      NOT NULL,  
            `id`     VARCHAR(50)      NOT NULL,   
            `password`  VARCHAR(50)    NOT NULL,
            `school`     VARCHAR(50)   NOT NULL,
            `gender`     VARCHAR(50)   NOT NULL,
            `age`     VARCHAR(50)   NOT NULL,
            `profile_image` VARCHAR(255)
        );""")

cursor.execute("""
    CREATE TABLE files (
        file_id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        board_id INT NOT NULL,
        filename VARCHAR(255),
        filepath VARCHAR(255)
    );
""")
conn.commit() 


name = ""
text = ""

@app.route("/", methods=['GET', 'POST'])
def main():
    
    if request.method == 'POST':

        search_text = request.form.get("search_text")
        search_type = request.form.get("search_type")

        if search_type == "title":
            cursor.execute("SELECT * FROM board WHERE title LIKE %s", (f'%{search_text}%',))
        elif search_type == "content":
            cursor.execute("SELECT * FROM board WHERE content LIKE %s", (f'%{search_text}%',))
        else:
            cursor.execute("SELECT * FROM board WHERE title LIKE %s OR content LIKE %s", 
                           (f'%{search_text}%', f'%{search_text}%'))
        posts = cursor.fetchall()
        
    
    else :
        cursor.execute("SELECT * FROM board")
        conn.commit()
        posts = cursor.fetchall()
        
    return render_template("main.html", posts=posts)


@app.route("/read/<index>", methods=['GET', 'POST']) 
def read(index):     
    cursor.execute("SELECT secret, secret_password FROM board WHERE board_id = %s", (index))
    post_info = cursor.fetchone()
    print(post_info[0])
    print(post_info[1])
    print(post_info)
    if post_info and post_info[0]:  # 비밀글 판별
        if request.method == 'POST':
            # 입력된 비밀번호 확인
            input_password = request.form.get('password')
            print(input_password)
            if input_password == post_info[1]:  # 비밀번호가 일치하는 경우
                cursor.execute("SELECT * FROM board WHERE board_id = %s", (index))
                posts = cursor.fetchall()
                cursor.execute("SELECT * FROM files WHERE board_id = %s", (index))
                files = cursor.fetchall()
                return render_template("read.html", posts=posts, files = files)
            else :
                return redirect('/')
        # GET 요청인 경우 비밀번호 입력 페이지 표시
        return render_template("secret_password.html", index=index)
    
    cursor.execute(f"SELECT * FROM board WHERE board_id = {index}")
    posts = cursor.fetchall()
    cursor.execute("SELECT * FROM files WHERE board_id = %s", (index))
    files = cursor.fetchall()

    return render_template("read.html", posts = posts, files = files)


@app.route('/file_download/<file_id>')
def download_file(file_id):

    cursor.execute("SELECT filepath, filename FROM files WHERE file_id = %s", (file_id))
    conn.commit()
    file = cursor.fetchone()
    
    if not file:
        print("파일을 찾을 수 없습니다")
        return "파일을 찾을 수 없습니다", 404
    

    return send_file( path_or_file=file[0],download_name=file[1],as_attachment=True,mimetype='application/octet-stream')



@app.route("/signup", methods=['GET', 'POST'])
def signup():
    
    if request.method == 'POST':
        nick = request.form.get("nick")
        id = request.form.get("id")
        password = request.form.get("password")
        school = request.form.get("school")
        gender = request.form.get("gender")
        age = request.form.get("age")
        cursor.execute("INSERT INTO login (nick, id, password, school, gender, age) VALUES (%s, %s, %s, %s, %s, %s)", (nick, id, password, school, gender, age))

        return redirect('/')
    return render_template("signup.html")



@app.route("/login", methods=['GET', 'POST'])
def login():
     
    if request.method == 'POST':
        id = request.form.get('id')
        password = request.form.get('password')
        cursor.execute("SELECT * FROM login WHERE id = %s AND password = %s", (id, password))
        user = cursor.fetchall()

        if user:
            # 세션에 사용자 정보 저장
            session['user_id'] = id 
            session['password'] = password # nick 저장
            return redirect('/')
        else:
            return render_template("login.html", error="아이디 또는 비밀번호가 일치하지 않습니다")
    
    return render_template("login.html")

@app.route("/logout", methods=['GET', 'POST'])
def logout():
    session.pop('user_id', None)
    session.pop('password', None)
    return redirect('/')



@app.route("/update/<index>", methods=['GET', 'POST'])
def update(index):
    
    if request.method == 'POST':
        new_title = request.form.get("title")
        new_content = request.form.get("content")
        cursor.execute("UPDATE board SET title=%s, content=%s WHERE board_id=%s", (new_title, new_content, index))
        conn.commit()

        return redirect(f'/read/{index}')
    
    return render_template("update.html")




@app.route("/delete/<index>")
def delete(index):
    cursor.execute(f"DELETE FROM board WHERE board_id = {index}")
    posts = cursor.fetchall()
    return redirect('/')



@app.route("/write", methods=['GET', 'POST'])
def write(): 
    if request.method == 'POST':
        name = request.form.get("name")
        text = request.form.get("text")
        secret = request.form.get("secret")
        secret_password = request.form.get("secret_password")
        
        cursor.execute("INSERT INTO board (title, content, secret, secret_password) VALUES (%s, %s, %s, %s)", 
                      (name, text, secret, secret_password))
        conn.commit()
        board_id = cursor.lastrowid

        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename != '':
                filename = file.filename
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                cursor.execute("INSERT INTO files (board_id, filename, filepath) VALUES (%s, %s, %s)", 
                             (board_id, filename, file_path))
                conn.commit()

        return redirect('/')
    return render_template("write.html")



@app.route("/mypage", methods=['GET', 'POST'])
def mypage():
    if 'user_id' not in session:
        return redirect('/login')
    
    cursor.execute("SELECT * FROM login WHERE id = %s", (session['user_id'],))
    conn.commit()
    user = cursor.fetchone()
    
    if request.method == 'POST':
        if 'profile_image' in request.files:
            file = request.files['profile_image']
            if file and file.filename != '':
                filename = f"{session['user_id']}_{file.filename}"
                file_path = os.path.join(PROFILE_UPLOAD_FOLDER, filename)
                file.save(file_path)
                
                cursor.execute("UPDATE login SET profile_image = %s WHERE id = %s", 
                             (filename, session['user_id']))
                conn.commit()
        return redirect('/mypage')
    
    return render_template("mypage.html", user=user)

@app.route('/profile_image/<filename>')
def profile_image(filename):
    return send_file(f'profile_images/{filename}')

    # user = cursor.fetchone()
    # if request.method == 'POST':
    #     return redirect('/mypage_update')
    # else :
    #     return render_template("mypage.html", user=user)
    
@app.route("/id_search", methods=['GET', 'POST'])
def id_search():
    if request.method == 'POST':
        nick = request.form.get("nick","")
        password = request.form.get("password","")

        cursor.execute("SELECT * FROM login WHERE password = %s, nick=%s ", (nick,session['user_id'], password))
        conn.commit()
        user_id = cursor.fetchone()

        if user_id:
            # ID를 찾아 사용자에게 표시
            return render_template("id_search.html", found_id=user_id[0])
        else:
            # ID를 찾지 못한 경우
            return render_template("id_search.html", error="닉네임 또는 비밀번호가 잘못되었습니다.")
    else : 
        return render_template("id_search.html")


@app.route("/mypage_update", methods=['GET', 'POST'])
def mypage_update():

    if request.method == 'POST':
        nick = request.form.get("nick","")
        school = request.form.get("school","")
        gender = request.form.get("gender","")
        password = request.form.get("password","")
        age = request.form.get("age","")
        cursor.execute("UPDATE login SET nick=%s, id=%s, password=%s, school=%s, gender=%s, age=%s WHERE id=%s", (nick,session['user_id'], password, school, gender, age, session['user_id']))
        conn.commit()

        return redirect("/mypage")
    else : 
        return render_template("mypage_update.html")

if __name__ == "__main__":
    app.run(debug=True)