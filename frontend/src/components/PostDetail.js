import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';

const PostDetail = () => {
  const { id } = useParams();
  const [post, setPost] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchPost = async () => {
      try {
        const response = await fetch(`http://localhost:3001/api/posts/${id}`);
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        setPost(data);
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    };

    fetchPost();
  }, [id]);

  if (loading) {
    return <div className="loading">Loading post...</div>;
  }

  if (error) {
    return <div className="error">Error: {error.message}</div>;
  }

  if (!post) {
    return <div className="error">Post not found.</div>;
  }

  return (
    <div className="post-detail-page">
      <header>
        <h1>{post.title}</h1>
        <nav>
          <Link to="/" className="nav-link">Back to Home</Link>
        </nav>
      </header>
      <main>
        <article className="post-content-full">
          {post.image && <img src={post.image} alt={post.title} className="post-image-full" />}
          <p className="post-timestamp">{new Date(post.timestamp).toLocaleString()}</p>
          <div dangerouslySetInnerHTML={{ __html: post.content }}></div>
        </article>
      </main>
    </div>
  );
};

export default PostDetail;
