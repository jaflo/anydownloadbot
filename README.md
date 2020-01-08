# AnyDownloadBot

Available on Telegram as [@AnyDownloadBot](http://t.me/AnyDownloadBot).

Send it a link and receive back a video or audio file to keep offline. Works with YouTube, SoundCloud, anything really. Hosted as an AWS Lambda function, built using [youtube-dl](https://github.com/ytdl-org/youtube-dl) and Python.

![Sample chat log](sample.png?raw=true)

## Usage

You can use the hosted version by chatting with [@AnyDownloadBot](http://t.me/AnyDownloadBot) on Telegram. Send a link to get back an audio file. Send the link with `/video` to get back the video. Telegram limits uploads to 50 MB, so a link to a download will be sent if needed.

## Installation

Install [serverless](https://serverless.com) and fill in your [Telegram token](https://core.telegram.org/bots#6-botfather) and [cutt.ly API keys](https://cutt.ly/cuttly-api) in the `.env` file.

Deploy the [ffmpeg-lambda-layer AWS Lambda layer](https://serverlessrepo.aws.amazon.com/applications/arn:aws:serverlessrepo:us-east-1:145266761615:applications~ffmpeg-lambda-layer) and update the `ffmpegBaseLayer` property in the `serverless.yml` file.

Run the following commands:

```
npm install
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
sls deploy
```

Update the webhook on Telegram by making a request to `http://api.telegram.org/bot[YOUR_BOT_TOKEN]/setWebhook?url=[AWS_ENDPOINT]` (you can just open it in your browser).

The completed URL should look like `http://api.telegram.org/bot0000000000:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa/setWebhook?url=https://0000000000.execute-api.us-east-0.amazonaws.com/dev/webhook` and you should get back an OK.
