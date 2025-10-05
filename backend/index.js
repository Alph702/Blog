require('dotenv').config({ path: './.env' });
const express = require('express');
const cors = require('cors');
const multer = require('multer');
const { createClient } = require('@supabase/supabase-js');
const path = require('path');

const app = express();
const port = process.env.PORT || 3001;

const supabaseUrl = process.env.SUPERBASE_URL;
const supabaseServiceRoleKey = process.env.SUPERBASE_SERVICE_ROLE_KEY;
const bucketName = process.env.SUPERBASE_S3_BUCKET_NAME;

const ADMIN_USERNAME = process.env.ADMIN_USERNAME;
const ADMIN_PASSWORD = process.env.ADMIN_PASSWORD;

const supabase = createClient(supabaseUrl, supabaseServiceRoleKey);

// Multer configuration for memory storage
const upload = multer({ storage: multer.memoryStorage() });

app.use(cors());
app.use(express.json());

// Simple authentication middleware
const authenticateAdmin = (req, res, next) => {
    const { username, password } = req.body;
    if (username === ADMIN_USERNAME && password === ADMIN_PASSWORD) {
        next();
    } else {
        res.status(401).json({ message: 'Unauthorized' });
    }
};

// Routes for posts
app.get('/api/posts', async (req, res) => {
    const { data, error } = await supabase
        .from('posts')
        .select('id, title, content, image, timestamp')
        .order('timestamp', { ascending: false });

    if (error) {
        return res.status(500).json({ error: error.message });
    }
    res.json(data);
});

app.get('/api/posts/:id', async (req, res) => {
    const { id } = req.params;
    const { data, error } = await supabase
        .from('posts')
        .select('id, title, content, image, timestamp')
        .eq('id', id)
        .single();

    if (error) {
        return res.status(500).json({ error: error.message });
    }
    if (!data) {
        return res.status(404).json({ message: 'Post not found' });
    }
    res.json(data);
});

// Admin login route
app.post('/api/login', authenticateAdmin, (req, res) => {
    res.json({ message: 'Login successful', admin: true });
});

// Route to create a new post
app.post('/api/posts', upload.single('image'), async (req, res) => {
    // Authentication check (can be a middleware)
    // For simplicity, assuming admin is logged in for now or handled by frontend

    const { title, content } = req.body;
    let imageUrl = null;

    if (req.file) {
        const file = req.file;
        const filename = `${Date.now()}-${file.originalname}`;
        const storagePath = `public/${filename}`;

        const { error: uploadError } = await supabase.storage
            .from(bucketName)
            .upload(storagePath, file.buffer, {
                contentType: file.mimetype,
                upsert: false,
            });

        if (uploadError) {
            console.error('Error uploading image:', uploadError.message);
            return res.status(500).json({ error: 'Failed to upload image' });
        }
        imageUrl = `${supabaseUrl}/storage/v1/object/public/${bucketName}/${storagePath}`.replace('anon', 'public');
    }

    const { data, error } = await supabase
        .from('posts')
        .insert({ title, content, image: imageUrl, timestamp: new Date().toISOString() });

    if (error) {
        return res.status(500).json({ error: error.message });
    }
    res.status(201).json(data);
});

// Route to update a post
app.put('/api/posts/:id', upload.single('image'), async (req, res) => {
    // Authentication check
    const { id } = req.params;
    const { title, content } = req.body;
    let imageUrl = req.body.image; // Keep existing image if not new one uploaded

    if (req.file) {
        const file = req.file;
        const filename = `${Date.now()}-${file.originalname}`;
        const storagePath = `public/${filename}`;

        const { error: uploadError } = await supabase.storage
            .from(bucketName)
            .upload(storagePath, file.buffer, {
                contentType: file.mimetype,
                upsert: true, // Overwrite if file exists (though filename is unique)
            });

        if (uploadError) {
            console.error('Error uploading image:', uploadError.message);
            return res.status(500).json({ error: 'Failed to upload image' });
        }
        imageUrl = `${supabaseUrl}/storage/v1/object/public/${bucketName}/${storagePath}`.replace('anon', 'public');
    }

    const { data, error } = await supabase
        .from('posts')
        .update({ title, content, image: imageUrl })
        .eq('id', id);

    if (error) {
        return res.status(500).json({ error: error.message });
    }
    res.json(data);
});

// Route to delete a post
app.delete('/api/posts/:id', async (req, res) => {
    // Authentication check
    const { id } = req.params;

    // Optional: Delete image from storage first
    // const { data: postData, error: fetchError } = await supabase.from('posts').select('image').eq('id', id).single();
    // if (postData && postData.image) {
    //     const filename = path.basename(postData.image);
    //     await supabase.storage.from(bucketName).remove([`public/${filename}`]);
    // }

    const { error } = await supabase
        .from('posts')
        .delete()
        .eq('id', id);

    if (error) {
        return res.status(500).json({ error: error.message });
    }
    res.status(204).send(); // No content
});

app.listen(port, () => {
  console.log(`Backend server listening at http://localhost:${port}`);
});