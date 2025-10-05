require('dotenv').config({ path: './.env' });
const { createClient } = require('@supabase/supabase-js');
const fs = require('fs').promises;
const path = require('path');

const supabaseUrl = process.env.SUPERBASE_URL;
const supabaseServiceRoleKey = process.env.SUPERBASE_SERVICE_ROLE_KEY;
const supabaseAnonKey = process.env.SUPERBASE_ANON_KEY; // Needed for public URL generation
const bucketName = process.env.SUPERBASE_S3_BUCKET_NAME;

const supabase = createClient(supabaseUrl, supabaseServiceRoleKey);

const UPLOAD_FOLDER = path.join(__dirname, '..', 'static', 'uploads');

async function migrateImages() {
    console.log('Starting image migration...');

    // 1. Fetch all posts from Superbase
    const { data: posts, error: fetchError } = await supabase
        .from('posts')
        .select('id, image');

    if (fetchError) {
        console.error('Error fetching posts from Superbase:', fetchError.message);
        return;
    }

    for (const post of posts) {
        if (post.image && !post.image.startsWith('http')) { // Check if image path is local
            const localImagePath = path.join(__dirname, '..', post.image);
            const filename = path.basename(post.image);
            const storagePath = `public/${filename}`; // Path in Superbase Storage

            try {
                const imageBuffer = await fs.readFile(localImagePath);

                // 2. Upload image to Superbase Storage
                const { data: uploadData, error: uploadError } = await supabase.storage
                    .from(bucketName)
                    .upload(storagePath, imageBuffer, {
                        contentType: 'image/jpeg', // Adjust content type based on actual file type
                        upsert: true // Overwrite if file exists
                    });

                if (uploadError) {
                    console.error(`Error uploading image ${filename} for post ID ${post.id}:`, uploadError.message);
                    continue;
                }

                // 3. Get public URL
                // Superbase storage public URL format: {supabaseUrl}/storage/v1/object/public/{bucketName}/{storagePath}
                const publicUrl = `${supabaseUrl}/storage/v1/object/public/${bucketName}/${storagePath}`.replace('anon', 'public');

                // 4. Update post in Superbase with new S3 URL
                const { error: updateError } = await supabase
                    .from('posts')
                    .update({ image: publicUrl })
                    .eq('id', post.id);

                if (updateError) {
                    console.error(`Error updating image URL for post ID ${post.id}:`, updateError.message);
                } else {
                    console.log(`Successfully migrated image for post ID ${post.id} to ${publicUrl}.`);
                }

            } catch (readError) {
                console.error(`Error reading local image file ${localImagePath} for post ID ${post.id}:`, readError.message);
            }
        }
    }
    console.log('Image migration complete.');
}

migrateImages();
