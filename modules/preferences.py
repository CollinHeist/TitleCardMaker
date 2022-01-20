# Global Preferences

imagemagick_docker_id: str = None

def update_imagemagick_docker_id(to: str) -> None:
    global imagemagick_docker_id
    imagemagick_docker_id = to