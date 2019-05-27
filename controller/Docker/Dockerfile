FROM debian:stretch-slim
MAINTAINER Andrea

#============================#
# Information & Requirements #
#============================#
# *** Run vlc in a container ***
#
# docker run -d --name vlc \
#   -v ${HOME}:/home/vlc \
#   -v /tmp/.X11-unix/:/tmp/.X11-unix/ \
#   -v /dev/snd:/dev/snd \
#   -v /dev/shm:/dev/shm \
#   -v /var/run/dbus:/var/run/dbus \
#   -e PULSE_SERVER=unix:${XDG_RUNTIME_DIR}/pulse/native \
#   -v ${XDG_RUNTIME_DIR}/pulse/native:${XDG_RUNTIME_DIR}/pulse/native \
#   --group-add $(getent group audio | cut -d: -f3) \   \\ optional
#   -e DISPLAY \
#   image

# VARIABLES
ENV USER vlc

#==============#
# Basics & VLC #
#==============#
RUN apt-get update && apt-get install --no-install-recommends -y \
    sudo \
        libgl1-mesa-dri \
        libgl1-mesa-glx \
        vlc &&

#=====================#
# VLC: Dedicated User #
#=====================#
ENV HOME /home/${USER}
RUN useradd -d ${HOME} -m ${USER} && \
    passwd -d ${USER} && \
    adduser ${USER} sudo
# SELECTION USER
USER ${USER}
# SELECTION STORAGE
WORKDIR ${HOME}

# NETTOYAGE
RUN sudo apt-get --purge autoremove -y && \
    sudo apt-get autoclean -y && \
    sudo rm /etc/apt/sources.list && \
    sudo rm -rf /var/cache/apt/archives/* && \
    sudo rm -rf /var/lib/apt/lists/*

CMD vlc
