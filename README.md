# Blog Project

Welcome to the **Flask Blog Project**! 🚀 This is a simple blogging platform built using Flask, allowing users to create, read, and manage blog posts.

## Features
- 📝 Create and manage blog posts
- 📅 Timestamped posts
- 🖼️ Image upload support
- 🔒 Admin login for secure access
- 🎨 Hacker-themed dark UI

---

## Installation & Setup

## Installation & Setup
```sh
 git clone https://github.com/Alph702/Blog.git
 cd Blog
```

```sh
 python -m venv venv
 source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

```sh
 pip install -r requirements.txt
```
```sh
 rm Blog.db
```

```sh
 python app.py
```
Your blog should be running at **http://127.0.0.1:8080/** 🎉

---

## Deployment on PythonAnywhere
Create an account on [PythonAnywhere](https://www.pythonanywhere.com/) and log in.

- Navigate to the **Web** tab
- Click **Add a new web app**
- Select **Flask** and choose the latest Python version

- Navigate to the **Files** tab
- Upload your project files (or clone from GitHub using `git clone` in a **Bash Console**)

- Go to **Web** → Edit the WSGI configuration file
- Modify it to include:
```python
import sys
sys.path.insert(0, '/home/yourusername/Blog')  # Change to your PythonAnywhere username

from app import app as application
```

Open a **Bash Console** and run:
```sh
 pip install -r /home/yourusername/Blog/requirements.txt --user
```

Go to the **Web** tab and click **Reload**. Your blog is now live! 🎉

---

Feel free to fork the repository, submit issues, or contribute to improve this project. 🚀

This project is open-source and licensed under the **MIT License**.
