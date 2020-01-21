import requests
import glob
import json
import os
import sys
import signal
from urllib.parse import urlparse
import subprocess
import boto3

TASK_QUEUE = os.environ["TASK_QUEUE"]
TELEGRAM_TOKEN = os.environ["TELEGRAM_TOKEN"]
CUTTLY_API_KEY = os.environ["CUTTLY_API_KEY"]
BASE_URL = "https://api.telegram.org/bot{}".format(TELEGRAM_TOKEN)

sys.path.insert(1, "/tmp")
os.environ["PATH"] += ":"+os.path.dirname(os.path.abspath(__file__))+"/bin"


def enqueue(event, context):
    if "body" not in event:
        return {
            "statusCode": 500,
            "body": json.dumps({
                "message": "Missing required fields.",
            })
        }

    data = json.loads(event["body"])
    message = str(data["message"]["text"])
    chat_id = data["message"]["chat"]["id"]
    message_id = data["message"]["message_id"]
    first_name = data["message"]["chat"]["first_name"]

    if "/start" == message:
        response = "Hi {}! Send a URL that you want to download and I'll send you the audio so you can keep it offline." + \
            "If you want the video, send /video and the link.".format(
                first_name)
    else:
        url = message.replace("@AnyDownloadBot", "")\
            .replace("/video", "").strip()

        if not url or not urlparse(url).scheme:
            response = "That doesn't look like a valid link."
        else:
            sqs = boto3.resource("sqs")
            queue = sqs.get_queue_by_name(QueueName=TASK_QUEUE)
            output = "video" if "/video" in message else "audio"

            queue.send_message(MessageBody=json.dumps({
                "chat_id": chat_id,
                "message_id": message_id,
                "output_type": output,
                "url": url
            }))

            response = "I'll grab the "+output+" and send it over in a bit."

    data = {"text": response.encode("utf8"), "chat_id": chat_id}
    requests.post(BASE_URL + "/sendMessage", data)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Processed message.",
        })
    }


def transfer(event, context):
    payload = json.loads(event["Records"][0]["body"])
    output_type = payload["output_type"]
    message_id = payload["message_id"]
    chat_id = payload["chat_id"]
    url = payload["url"]

    signal.alarm((context.get_remaining_time_in_millis() // 1000) - 1)
    data = {
        "chat_id": chat_id,
        "reply_to_message_id": message_id,
    }

    try:
        subprocess.run("./deps.sh")
        import youtube_dl

        codec = ""
        ydl_opts = {
            "quiet": True,
            "noplaylist": True,
            "outtmpl": "/tmp/%(title)s.%(ext)s",
            "cachedir": "/tmp"
        }

        if output_type == "video":
            codec = "mp4"
            ydl_opts.update({
                "format": "bestvideo[vcodec*=h264,vcodec*=mp4][filesize<47M]+bestaudio[vcodec*=aac,vcodec*=mp3][filesize<47M]/best[ext=mp4][filesize<47M]",
                "postprocessors": [{
                    "key": "FFmpegVideoConvertor",
                    "preferedformat": codec
                }]
            })
        elif output_type == "audio":
            codec = "mp3"
            ydl_opts.update({
                "format": "bestaudio[filesize<47M]/best[filesize<47M]",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": codec,
                    "preferredquality": "192"
                }]
            })
        else:
            return "Invalid request."

        was_successful = True
        try:
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([url])
        except:
            was_successful = False

        if was_successful:
            filename = max(glob.glob("/tmp/*." + codec), key=os.path.getctime)
            filesize = os.path.getsize(filename)
            # 50 MB is Telegram's limit (as of Jan 2020)
            if filesize < 50*1000*1000:
                response = requests.post(BASE_URL + "/send" + output_type,
                                         files={output_type: open(
                                             filename, "rb")},
                                         data={
                                             "supports_streaming": True,
                                             "chat_id": chat_id,
                                             "reply_to_message_id": message_id
                                         })
                return "Success!"

        media_url = None
        with youtube_dl.YoutubeDL({
            "quiet": True,
            "noplaylist": True,
            "format": "best"
        }) as ydl:
            r = ydl.extract_info(url, download=False)
            media_url = r["formats"][-1]["url"]
            media_url = requests.get("https://cutt.ly/api/api.php", params={
                "key": CUTTLY_API_KEY,
                "short": media_url
            }).json()["url"]["shortLink"]

        if media_url:
            data.update({
                "text": "I can't send the file directly, but you can try downloading it here: {}".format(media_url)
            })
    except TimeoutException:
        data.update({
            "text": "The file took too long to retrieve.",
        })
    except Exception as e:
        data.update({
            "text": "An error occurred while retrieving the file:\n```{}```".format(str(e).strip()),
            "parse_mode": "markdown"
        })
        requests.post(BASE_URL + "/sendMessage", data)
        raise e

    requests.post(BASE_URL + "/sendMessage", data)
    return "Couldn't extract."


class TimeoutException(Exception):
    pass


def timeout_handler(_signal, _frame):
    raise TimeoutException("Time exceeded")


signal.signal(signal.SIGALRM, timeout_handler)
