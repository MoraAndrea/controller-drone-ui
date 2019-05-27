FROM debian

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && \
	apt-get install -y --no-install-recommends \
		ca-certificates \
		libgl1-mesa-dri \
		libgl1-mesa-glx \
		pulseaudio \
		alsa-utils \
		dbus* \
		vlc vlc-plugin-access-extra vlc-plugin-notify vlc-plugin-jack &&\
	apt-get -y -f install && \
	useradd -m vlc && \
	usermod -a -G audio,video vlc && \
	rm -rf /var/lib/apt/lists/*

USER vlc

WORKDIR /home/vlc/media
