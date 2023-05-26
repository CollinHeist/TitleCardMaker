# Getting Started - Docker Tutorial
## Background
Docker is a very convenient way of compartmentalizing a piece of software,
in this case TitleCardMaker, from the rest of your host machine. It also
has the benefit of coming pre-packaged with all the required
dependent software, making installation much easier.

Because of this, Docker is the recommended installation method for all
Operating Systems.

For [UnRAID](../docker/unraid.md) and [Synology](../docker/synology.md)
DSM users, there are OS-specific tutorials written to walk you through
the installation process. All other systems should follow the [standard
tutorial](../docker/docker.md). 

??? warning "Warning for Cross-OS Compatiblity"

    Attempting to run the different components of TitleCardMaker across
    different Operating Systems can cause a lot of headache. In
    particular, if Sonarr is running on a Windows machine while
    TitleCardMaker is running within a Docker container. If possible, it
    is recommended to run both Sonarr _and_ TitleCardMaker in separate
    Docker containers.

    Whether your media server(s) (Plex, Emby, and Jellyfin) are running
    in a Docker container is significantly less important.

    