#!/bin/sh

cd /tmp
rm -rf *

release=$(curl https://yt-dl.org | grep -Eo 'downloads[^\"]+gz')
curl -sL https://yt-dl.org/$release -o youtube-dl.tar.gz

tar -xf youtube-dl.tar.gz
mv youtube-dl*/youtube_dl youtube_dl
