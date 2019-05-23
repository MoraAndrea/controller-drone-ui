from os import path
import yaml


def modifiedIp_vlcGUI(defaultFile, ip):
    # open default yaml document
    with open(path.join(path.dirname(__file__), defaultFile)) as f:
        list_doc = yaml.safe_load(f)

    # edit field
    list_doc['spec']['containers'][0]['args'][0] = "vlc -V x11 http://" + ip + ":8080 " \
                                                                               "--no-qt-privacy-ask " \
                                                                               "--no-metadata-network-access " \
                                                                               "--snapshot-path=/home/vlc/snapshots " \
                                                                               "--network-caching=1000"

    # write a yaml document
    with open("FileGuiMod.yaml", "w") as f:
        yaml.dump(list_doc, f)
    return "FileGuiMod.yaml"


def modified_videoToStream(defaultFile, videoPath):
    # open default yaml document
    with open(path.join(path.dirname(__file__), defaultFile)) as f:
        list_doc = yaml.safe_load(f)

    # edit field
    list_doc['spec']['containers'][0]['args'][0] = "cvlc -vvv " + videoPath + " --sout " \
                                                                              "'#transcode{vcodec=h264,vb=1500,fps=35,width=640,height=360,acodec=mp3,ab=192,channels=2,samplerate=44100,scodec=none}" \
                                                                              ":http{mux=ffmpeg{mux=flv},dst=:8080/}' " \
                                                                              "--no-sout-all " \
                                                                              "--sout-keep"

    # write a yaml document
    with open("FileStreamMod.yaml", "w") as f:
        yaml.dump(list_doc, f)
    return "FileStreamMod.yaml"


def modified_localVideo(defaultFile, videoPath):
    # open default yaml document
    with open(path.join(path.dirname(__file__), defaultFile)) as f:
        list_doc = yaml.safe_load(f)

    # edit field
    list_doc['spec']['containers'][0]['args'][0] = "vlc " + videoPath

    # write a yaml document
    with open("FileLocalMod.yaml", "w") as f:
        yaml.dump(list_doc, f)
    return "FileLocalMod.yaml"


if __name__ == '__main__':
    pass
