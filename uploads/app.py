from flask import Flask, render_template, request, redirect, url_for
import pymysql

app = Flask(__name__)


conn = pymysql.connect(host='localhost', port=3306, user='root', passwd='1234', charset='utf8')

cursor = conn.cursor()

#cursor.execute("DROP DATABASE notice;") # TODO 2번째 실행부터 주석을 풀고 사용해주시면 감사하겠습니다.
cursor.execute("CREATE DATABASE notice;")
cursor.execute("USE notice;")

cursor.execute("CREATE TABLE board (`board_id` INT NOT NULL AUTO_INCREMENT PRIMARY KEY, `title` VARCHAR(50)      NOT NULL,  `content`     VARCHAR(1000)    NOT NULL);")
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
        return render_template("main.html", posts=posts)
    
    else :
        cursor.execute("SELECT * FROM board")
        conn.commit()
        posts = cursor.fetchall()

        return render_template("main.html", posts=posts)



@app.route("/read/<index>", methods=['GET'])
def read(index):     
    cursor.execute(f"SELECT * FROM board WHERE board_id = {index}")
    posts = cursor.fetchall()

    return render_template("read.html", posts = posts)





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
    global name, text

    if request.method == 'POST':
        name = request.form.get("name")
        text = request.form.get("text")

        cursor.execute("INSERT INTO board (title, content) VALUES (%s, %s)", (name, text))
        conn.commit()

        return redirect('/')
    
    return render_template("write.html")

if __name__ == "__main__":
    app.run(debug=True)