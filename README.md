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

### 1️⃣ Clone the Repository
```sh
 git clone https://github.com/Alph702/Blog.git
 cd Blog
```

### 2️⃣ Create a Virtual Environment
```sh
 python -m venv venv
 source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

### 3️⃣ Install Dependencies
```sh
 pip install -r requirements.txt
```

### 4️⃣ Run the Application Locally
```sh
 python app.py
```
Your blog should be running at **http://127.0.0.1:8080/** 🎉

---

## Deployment on PythonAnywhere

### 1️⃣ Sign up and Log in
Create an account on [PythonAnywhere](https://www.pythonanywhere.com/) and log in.

### 2️⃣ Set Up a New Web App
- Navigate to the **Web** tab
- Click **Add a new web app**
- Select **Flask** and choose the latest Python version

### 3️⃣ Upload Your Code
- Navigate to the **Files** tab
- Upload your project files (or clone from GitHub using `git clone` in a **Bash Console**)

### 4️⃣ Configure WSGI
- Go to **Web** → Edit the WSGI configuration file
- Modify it to include:
```python
import sys
sys.path.insert(0, '/home/yourusername/Blog')  # Change to your PythonAnywhere username

from app import app as application
```

### 5️⃣ Install Dependencies
Open a **Bash Console** and run:
```sh
 pip install -r /home/yourusername/Blog/requirements.txt --user
```

### 6️⃣ Restart the Web App
Go to the **Web** tab and click **Reload**. Your blog is now live! 🎉

---

## Contribution
Feel free to fork the repository, submit issues, or contribute to improve this project. 🚀

## License
This project is open-source and licensed under the **MIT License**.

---

Happy Coding! 😊

