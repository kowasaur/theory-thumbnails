from pyyoutube import Api, PlaylistItem
from disnake import ApplicationCommandInteraction
from disnake.ext import commands, tasks
from dotenv import load_dotenv
from os import getenv
import json
import random

GAME_THEORY = "UUo_IB5145EVNcf8hw1Kku7w"
FILM_THEORY = "UU3sznuotAs2ohg_U__Jzj_Q"
FOOD_THEORY = "UUHYoe8kQ-7Gn9ASOlmI0k6Q"
STYLE_THEORY = "UUd4t3EEUy0LUOM4MTdjpNHA"

try:
    with open("channels.json", "r") as f:
        channels = json.load(f)
except FileNotFoundError:
    channels = {}

load_dotenv()
api = Api(api_key=getenv("API"))
bot = commands.InteractionBot()


def get_thumbnail(video: PlaylistItem) -> str:
    res = video.snippet.thumbnails.maxres
    if res is None:
        res = video.snippet.thumbnails.medium
    assert res is not None, f"Thumbnail url not found for {video.snippet.title}"
    return res.url


def get_all_thumbnails() -> list[str]:
    return [
        get_thumbnail(v)
        for theory in [GAME_THEORY, FILM_THEORY, FOOD_THEORY, STYLE_THEORY]
        for v in api.get_playlist_items(playlist_id=theory, count=None).items
    ]


thumbnails = get_all_thumbnails()


async def next_thumbnail(inter: ApplicationCommandInteraction) -> None:
    time = send_daily_image.next_iteration.astimezone().strftime(
        "The next thumbnail will be sent in <#{}> at %H:%M on %Y-%m-%d")
    channel = channels[str(inter.guild_id)]
    await inter.response.send_message(time.format(channel))


@bot.event
async def on_ready():
    print(f"IT'S THEORING TIME with {len(thumbnails)} thumbnails")


@bot.slash_command(description="Manually get a random thumbnail")
async def image(inter: ApplicationCommandInteraction):
    await inter.response.send_message(random.choice(thumbnails))


@bot.slash_command(description="Set the bot to send images in this channel")
async def setup(inter: ApplicationCommandInteraction):
    channels[str(inter.guild_id)] = inter.channel_id  # str because of json
    with open("channels.json", "w") as f:
        json.dump(channels, f)

    await next_thumbnail(inter)


@bot.slash_command(description="Change the thumbnail frequency")
@commands.is_owner()
async def change_frequency(inter: ApplicationCommandInteraction, hours: float):
    send_daily_image.change_interval(hours=hours)
    await next_thumbnail(inter)


@tasks.loop(hours=24)
async def send_daily_image():
    # So that it can get new videos without dealing with PubSubHubbub
    thumbnails = get_all_thumbnails()

    for _, channel in channels.items():
        await bot.get_channel(channel).send(random.choice(thumbnails))


@send_daily_image.before_loop
async def before_daily_images():
    await bot.wait_until_ready()


send_daily_image.start()
bot.run(getenv("TOKEN"))
