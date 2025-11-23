from supabase import create_client, Client
from config import Config


# Repositories
from repositories import PostRepository
from repositories import UserRepository
from repositories import VideoRepository

# Services
from services import AuthService
from services import PostService
from services import VideoService
from services import WorkerService

# Validate essential environment variables
env_names: list[str] | None = []
for env in [
    Config.SUPABASE_URL,
    Config.SUPABASE_KEY,
    Config.SECRET_KEY,
    Config.ADMIN_USERNAME,
    Config.ADMIN_PASSWORD,
    Config.BLOG_IMAGES_BUCKET,
    Config.BLOG_VIDEOS_BUCKET,
]:
    if env == "UNDEFINED":
        env_names.append(env)
if env_names:
    raise EnvironmentError(f"Missing environment variables: {', '.join(env_names)}")

# Initialize Supabase Client
supabase_client: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

# Initialize Repositories
post_repo: PostRepository = PostRepository(supabase_client)
user_repo: UserRepository = UserRepository(supabase_client)
video_repo: VideoRepository = VideoRepository(supabase_client)

# Initialize Services
auth_service: AuthService = AuthService(user_repo)
worker_service: WorkerService = WorkerService(
    supabase_client, Config.BLOG_VIDEOS_BUCKET
)
video_service: VideoService = VideoService(video_repo, worker_service)
post_service: PostService = PostService(post_repo, video_service)
