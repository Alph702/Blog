from supabase import create_client, Client
from config import Config
import logging


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
required_env_vars = {
    "SUPABASE_URL": Config.SUPABASE_URL,
    "SUPABASE_KEY": Config.SUPABASE_KEY,
    "SECRET_KEY": Config.SECRET_KEY,
    "ADMIN_USERNAME": Config.ADMIN_USERNAME,
    "ADMIN_PASSWORD": Config.ADMIN_PASSWORD,
    "BLOG_IMAGES_BUCKET": Config.BLOG_IMAGES_BUCKET,
    "BLOG_VIDEOS_BUCKET": Config.BLOG_VIDEOS_BUCKET,
}

missing_env_vars: list[str] = [
    name for name, value in required_env_vars.items() if value == "UNDEFINED"
]

if missing_env_vars:
    raise EnvironmentError(
        f"Missing environment variables: {', '.join(missing_env_vars)}"
    )

# Initialize Supabase Client
supabase_client: Client = create_client(Config.SUPABASE_URL, Config.SUPABASE_KEY)

# Module logger for container
logger = logging.getLogger(__name__)
logger.info("Container initialized: Supabase client and components created")

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
