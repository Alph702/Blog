require('dotenv').config({ path: './.env' });
const sqlite3 = require('sqlite3').verbose();
const { createClient } = require('@supabase/supabase-js');

const supabaseUrl = process.env.SUPERBASE_URL;
const supabaseServiceRoleKey = process.env.SUPERBASE_SERVICE_ROLE_KEY;

const supabase = createClient(supabaseUrl, supabaseServiceRoleKey);

const db = new sqlite3.Database('../blog.db', sqlite3.OPEN_READONLY, (err) => {
    if (err) {
        console.error('Error connecting to SQLite database:', err.message);
    } else {
        console.log('Connected to the SQLite blog.db database.');
    }
});

async function migrateData() {
    console.log('Starting data migration...');
    db.all('SELECT id, title, content, image, timestamp FROM posts', async (err, rows) => {
        if (err) {
            console.error('Error querying SQLite:', err.message);
            return;
        }

        for (const row of rows) {
            // Superbase will auto-generate ID if not provided, but we want to keep original IDs
            // However, if `id` is a SERIAL type in Superbase, we might need to handle this differently
            // For now, let's try inserting with ID. If it fails, we'll remove `id` from insert.
            const { data, error } = await supabase
                .from('posts')
                .insert({
                    id: row.id,
                    title: row.title,
                    content: row.content,
                    // Image path needs to be handled separately for S3 migration
                    // For now, we'll insert the old path, and update it after S3 migration
                    image: row.image,
                    timestamp: row.timestamp
                });

            if (error) {
                console.error(`Error inserting post ID ${row.id} into Superbase:`, error.message);
            } else {
                console.log(`Successfully migrated post ID ${row.id}.`);
            }
        }
        console.log('Data migration complete.');
        db.close();
    });
}

migrateData();
