# Blog Platform Project Description

## 1. Project Title
**Hacker-Themed Flask Blog Platform**

## 2. Overview/Purpose
This project is a simple, yet functional, blogging platform built using the Flask web framework. Its primary purpose is to provide a robust and easy-to-manage system for creating, publishing, and viewing blog posts. The platform features a distinctive hacker-themed dark user interface, offering a unique aesthetic experience. It's designed for individuals or small teams who want a straightforward way to share content online with minimal overhead, leveraging modern cloud services for data persistence and asset storage.

## 3. Key Features
*   **Blog Post Management**:
    *   **Create New Posts**: Admin users can create new blog posts with titles, content, and optional images.
    *   **View Posts**: Users can browse and read individual blog posts.
    *   **Admin Dashboard**: A protected area for administrators to manage blog content.
*   **User Authentication**:
    *   **Admin Login**: Secure login system for administrators to access content management features.
*   **Content Storage**:
    *   **Supabase Integration**: Utilizes Supabase for both database (PostgreSQL) and image storage, providing a scalable and reliable backend.
    *   **Local Fallback for Images**: During development or in specific deployment scenarios, images can be served from a local `static/uploads` directory.
*   **Dynamic Frontend**:
    *   **Jinja2 Templating**: All frontend views are dynamically rendered using Jinja2 templates, ensuring a consistent and maintainable UI.
    *   **Hacker-Themed UI**: A custom dark theme (`static/style.css`) provides a distinct visual identity.
*   **Responsive Design**: Basic responsiveness for viewing on different devices.

## 4. Technology Stack

### Backend
*   **Flask**: The micro web framework for Python, forming the core of the application's backend. Handles routing, request processing, and view rendering.
*   **python-dotenv**: Manages environment variables, allowing for secure configuration without hardcoding sensitive information.
*   **pytz & python-dateutil**: Used for robust timezone handling and parsing of date/time strings, ensuring accurate timestamp display.
*   **Werkzeug**: A comprehensive WSGI utility library that Flask is built upon, providing tools for HTTP requests, responses, and utilities.
*   **MarkupSafe**: Implements a `Markup` string type that escapes unsafe characters to prevent Cross-Site Scripting (XSS) attacks when rendering templates.
*   **requests**: A popular HTTP library for making API calls, primarily used for interacting with the Supabase API.

### Database & Storage
*   **Supabase**:
    *   **PostgreSQL Database**: Provides the relational database for storing blog post data (titles, content, timestamps, etc.). Accessed via `psycopg2-binary`.
    *   **Supabase Storage**: Used for storing uploaded images associated with blog posts, offering a CDN-backed solution.

### Frontend
*   **Jinja2**: The templating engine used by Flask to render dynamic HTML pages.
*   **HTML5**: Standard markup language for creating web pages.
*   **CSS3 (`static/style.css`)**: Custom styles to achieve the hacker-themed dark UI.
*   **JavaScript (`static/script.js`)**: For any client-side interactivity and dynamic behavior.

### Testing
*   **pytest**: A powerful and flexible testing framework for Python, used for writing unit and integration tests.
*   **pytest-playwright**: A plugin for `pytest` that enables end-to-end testing of web applications using Playwright, ensuring the UI and user flows function correctly.

## 5. Architecture
The application follows a **monolithic architecture** with a clear separation of concerns:

*   **`app.py`**: This is the main application file. It defines all the routes, handles HTTP requests, interacts with the Supabase backend (both database and storage), processes form submissions, and renders the appropriate Jinja2 templates. It acts as the central orchestrator.
*   **`templates/` Directory**: Contains all the Jinja2 HTML templates (`index.html`, `post.html`, `new.html`, `login.html`). These templates define the structure and layout of the web pages, with dynamic content injected by Flask.
*   **`static/` Directory**: Stores all static assets, including:
    *   `style.css`: The main stylesheet for the application's visual design.
    *   `script.js`: Client-side JavaScript for interactive elements.
    *   `uploads/`: A directory for locally stored images, serving as a fallback or for development purposes when Supabase Storage is not fully configured.
    *   `arrow.svg`, `favicon.ico`, `full-screen.svg`: Other static assets like icons.
*   **`.env` File**: Stores sensitive configuration details and API keys, ensuring they are not committed to version control.
*   **`tests/` Directory**: Contains all test files (`test_blog.py`, `conftest.py`) for verifying the application's functionality.

The data flow typically involves:
1.  A user's browser sends an HTTP request to the Flask application.
2.  `app.py` processes the request, potentially interacting with Supabase for data retrieval or storage.
3.  `app.py` renders a Jinja2 template, passing dynamic data to it.
4.  The rendered HTML, along with static assets (CSS, JS), is sent back to the user's browser.

## 6. Setup and Installation

### Prerequisites
*   Python 3.8+
*   `pip` (Python package installer)
*   A Supabase project with a configured PostgreSQL database and Storage bucket.

### Steps
1.  **Clone the Repository**:
    ```bash
    git clone <repository_url>
    cd blog
    ```
2.  **Create a Virtual Environment**:
    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    ```
3.  **Install Dependencies**:
    ```bash
    pip install -r requirements.txt
    ```
4.  **Configure Environment Variables**:
    Create a `.env` file in the project root with your Supabase and admin credentials:
    ```
    ADMIN_USERNAME=your_admin_username
    ADMIN_PASSWORD=your_admin_password
    SUPABASE_URL=your_supabase_project_url
    SUPABASE_KEY=your_supabase_anon_key_or_service_role_key
    BLOG_IMAGES_BUCKET=your_supabase_storage_bucket_name # e.g., blog_images
    ```
    **Note**: For production, use a `SUPABASE_SERVICE_ROLE_KEY` and ensure it's kept secret. For local development, the anon key might suffice.

5.  **Run the Application**:
    ```bash
    python app.py
    ```
    The application will be accessible at `http://127.0.0.1:8080/`.

## 7. Usage
*   **Homepage**: Navigate to `/` to view a list of all blog posts.
*   **View Post**: Click on a post title from the homepage to view the full content of an individual post.
*   **Admin Login**: Access the admin login page at `/login`. Use the `ADMIN_USERNAME` and `ADMIN_PASSWORD` configured in your `.env` file.
*   **Create New Post**: After logging in, navigate to `/new` to create a new blog post.

## 8. Development Guidelines
*   **Code Style**: Adhere to PEP 8 for Python code.
*   **Database Interactions**: All database operations should be handled through the Supabase client, ensuring proper error handling and data validation.
*   **Templating**: Keep Jinja2 templates clean and focused on presentation logic. Avoid complex business logic within templates.
*   **Testing**: Write unit tests for backend logic and end-to-end tests for critical user flows using `pytest` and `pytest-playwright`.
*   **Security**: Always sanitize user input and escape output to prevent common web vulnerabilities. Keep API keys and sensitive information out of version control.

## 9. Future Enhancements (Optional)
*   **User Registration/Multiple Authors**: Allow multiple users to register and create posts.
*   **Commenting System**: Implement a system for users to comment on blog posts.
*   **Tagging/Categories**: Add functionality to categorize and tag posts for better organization and searchability.
*   **Search Functionality**: Implement a search bar to find posts by keywords.
*   **Rich Text Editor**: Integrate a WYSIWYG editor for creating and editing post content.
*   **Pagination**: For a large number of posts, implement pagination on the homepage.
*   **Improved Error Handling**: More graceful error pages and logging.
*   **CI/CD Pipeline**: Automate testing and deployment processes.
