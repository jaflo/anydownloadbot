#!/bin/sh

cd /tmp
rm -rf *

curl -sL https://yt-dl.org/downloads/latest/youtube-dl -o youtube-dl
curl -sL https://github.com/ytdl-org/youtube-dl/archive/master.zip -o youtube-dl-master.zip

chmod a+rx youtube-dl
unzip -q youtube-dl-master.zip

mv youtube-dl-master/youtube_dl ytdl
rm -rf youtube-dl-master
rm -rf youtube_dl
mv ytdl youtube_dl
