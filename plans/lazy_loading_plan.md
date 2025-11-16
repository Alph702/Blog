# Plan: Implement Lazy Loading for Blog Posts

🌟 **Summary**

Optimize application performance and improve user experience by implementing lazy loading (load-on-scroll) for blog posts on the homepage and other listing pages.

🧩 **Problem or Motivation**

As the number of blog posts grows, loading all posts at once on the homepage can lead to slower page load times and a degraded user experience. Implementing load-on-scroll will fetch posts only when they are needed, improving initial load performance and perceived speed.

---

🧰 **Proposed Solution**

## 1. Backend (Flask)

### a. Paginated Post Retrieval

The main `index` route in `app.py` will be modified to accept `page` and `per_page` query parameters. This will allow for paginated fetching of posts from the Supabase database.

**Diagram: Backend Request Flow**

```ascii
+-----------------+      +-------------------------+      +------------------------+
| Client (Browser)|----->|   Flask App (app.py)    |----->|   Supabase (PostgreSQL)|
| GET /?page=2    |      |                         |      |                        |
+-----------------+      | @app.route('/')         |      | SELECT * FROM posts    |
                         | def index():            |      | ORDER BY timestamp DESC|
                         |     page = ...          |      | LIMIT 10 OFFSET 10;    |
                         |     per_page = ...      |      |                        |
                         |     posts = db.query()  |      +-----------+------------+
                         +-------------------------+                  |
                                   |                                  |
                         +-------------------------+                  |
                         |   Rendered HTML         |<-----------------+
                         | (or JSON for API)       |
                         +-------------------------+
                                   |
+-----------------+      +-------------------------+
| Client (Browser)|<-----|      Server Response    |
| (Receives posts)|      |                         |
+-----------------+      +-------------------------+
```

### b. API Endpoint for AJAX Requests

A new API endpoint, `/api/posts`, will be created to handle AJAX requests from the frontend. This endpoint will return a JSON object containing the posts for the requested page and information about whether more posts are available.

**Example JSON Response from `/api/posts?page=2`:**

```json
{
  "posts": [
    {
      "id": 15,
      "title": "Another Post",
      "content_preview": "This is a short preview...",
      "image": "/static/uploads/image.jpg",
      "timestamp": "2025-11-15"
    }
  ],
  "has_next": true
}
```

## 2. Frontend (JavaScript/Jinja2)

### a. Scroll Detection

JavaScript will be used to detect when the user scrolls near the bottom of the page. An event listener will trigger a function to load more posts.

### b. AJAX Request and Dynamic Loading

When the scroll threshold is reached, an AJAX `fetch` request will be sent to the `/api/posts` endpoint. A loading indicator will be shown to the user. Upon receiving the new posts, the JavaScript will render them as HTML elements and append them to the existing post list.

**Diagram: Frontend Interaction Flow**

```ascii
+----------------------+
|      User Scrolls    |
+----------+-----------+
           |
           v
+----------------------+
| JS: Near bottom of   |
| page? (Threshold)    |
+----------+-----------+
           | Yes
           v
+----------------------+
| JS: Show Loading     |
|      Spinner         |
+----------+-----------+
           |
           v
+----------------------+      +----------------------+
| JS: Fetch next page  |----->|  GET /api/posts?page=N |
| from API             |      +----------------------+
+----------+-----------+
           |
           v
+----------------------+      +----------------------+
| JS: Receive JSON     |<-----|   Flask API Response   |
+----------+-----------+      +----------------------+
           |
           v
+----------------------+
| JS: Hide Spinner     |
+----------+-----------+
           |
           v
+----------------------+
| JS: Render new posts |
| & Append to DOM      |
+----------+-----------+
           |
           v
+----------------------+
| JS: Increment page N |
+----------------------+
```

### c. Graceful End of Content

When the API response indicates `has_next: false`, the scroll listener will be disabled, and a message like "No more posts" will be displayed to the user.

---

📦 **Technical Considerations**

-   **Frontend:** Changes will be primarily in `static/js/script.js` and the main `templates/index.html` template.
-   **Backend:** Changes will be in `app.py`.
-   **Database:** The existing `posts` table schema is sufficient. The changes involve modifying the `SELECT` queries to use `LIMIT` and `OFFSET`.
-   **UI/UX:** A subtle loading indicator (e.g., a spinner) will be added to provide feedback during post loading. The "No more posts" message should be clear but unobtrusive.

---

🧠 **Alternatives**

-   **Traditional Pagination:** Implement "Next/Previous" buttons. This is simpler to implement but provides a less fluid user experience compared to infinite scrolling.
-   **"Load More" Button:** A button at the bottom of the list that the user clicks to load more posts. This is a good compromise between pagination and infinite scroll, giving the user more control.

For this project, the load-on-scroll approach is preferred as it aligns with a modern, seamless user experience.

---

🧾 **Additional Context**

This feature is a key scalability improvement. It ensures the application remains fast and responsive, regardless of the number of posts in the database, which is crucial for long-term content growth.
