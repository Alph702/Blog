import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';

const Home = () => {
  const [posts, setPosts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchPosts = async () => {
      try {
        const response = await fetch('http://localhost:3001/api/posts');
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setPosts(data);
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    };

    fetchPosts();
  }, []);

  if (loading) {
    return <div className="loading">Loading posts...</div>;
  }

  if (error) {
    return <div className="error">Error: {error.message}</div>;
  }

  return (
    <div className="home-page">
      <header>
        <h1>My Blog</h1>
        <nav>
          <Link to="/new" className="nav-link">New Post</Link>
          <Link to="/login" className="nav-link">Admin Login</Link>
        </nav>
      </header>
      <main>
        <div className="posts-list">
          {posts.map((post) => (
            <div key={post.id} className="post-card">
              <h2><Link to={`/post/${post.id}`}>{post.title}</Link></h2>
              {post.image && <img src={post.image} alt={post.title} className="post-image" />}
              <p className="post-timestamp">{new Date(post.timestamp).toLocaleString()}</p>
              <div className="post-content" dangerouslySetInnerHTML={{ __html: post.content.substring(0, 200) + '...' }}></div>
              <Link to={`/post/${post.id}`} className="read-more">Read More</Link>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
};

export default Home;
