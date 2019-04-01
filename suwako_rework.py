import os, re, sys, random, asyncio, discord, signal, traceback
from urllib.request import urlopen
from xml.etree import ElementTree
from random import randint
from pyquery import PyQuery

client = discord.Client()
data = {}
tag_weight = {}
url = 'http://gelbooru.com/index.php?page=dapi&s=post&q=index&tags='
source = None

"""
Get and return Gelbooru image
"""
def img(tags, user, nsfw):
    global source
    # Got to keep it legal.
    tags.append('-loli')
    tags.append('-shota')
    tags.append('-trap')

    if nsfw:
        tags.append('rating:explicit')
    else:
        tags.append('rating:safe')

    tags = '+'.join(tags)
    if data['debug']:
        print(''.join([url, tags]))
    posts = ElementTree.fromstring(urlopen(''.join([url, tags])).read())
    
    try:
        if posts.attrib['success'] == "false":
            return ''.join(["```Gelbooru says:\n    ", posts.attrib['reason'], "```"])
        
    except KeyError:
        pass

    if not posts:
        return "Nothing found using: %s"

    post = posts[randint(0, len(posts)-1)]

    source = post.attrib['source']
    post = post.attrib['file_url']

    return post

"""
On message event
"""
@client.event
async def on_message(message):
    if message.content.startswith(data['key']):
        user = message.author
        t = message.content.lower().split(' ')
        command = t[0].strip(data['key'])
        args = t[:-1]

        # Check command
        if command == 'img':
            response = img(args, user, False)
        elif command == 'eimg':
            response = img(args, user, True)
        elif command == 'source':
            if source:
                response = source
            else:
                response = None

        # Send response
        if response:
            await client.send_message(message.channel, response)

"""
Load configuration.
"""
try:
    with open('config.txt', 'r') as rw:
        try:
            data = {}
            for a in rw.readlines():
                b = a.strip('\n').split('=')
                data[b[0]] = b[1]
            data['debug'] = int(data['debug'])
            data['positive_reactions'] = data['positive_reactions'].split(',')
            data['negative_reactions'] = data['negative_reactions'].split(',')
            data['reaction_weight_mod'] = float(data['reaction_weight_mod'])

            if not os.path.exists('ratings'):
                os.makedirs('ratings')

            try:
                ratings = None
                with open('ratings/weights.txt', 'r') as rw:
                    for a in rw.read().split('\n'):
                        a = a.split(':')
                        tag_weight[a[0]] = float(a[1])

            except FileNotFoundError:
                pass

        except:
            if data['debug']:
                print(traceback.format_exc())
            print('Error loading configuration. Check configuration.')
            sys.exit(0)


    """
    Generate configuration file and ratings folder if not already existing.
    """
except FileNotFoundError:
    with open('config.txt', 'w') as rf:
        lines = '\n'.join(['token=[token]', 'key=$', 'debug=0', \
            'positive_reactions=wow,wau,hett,hot,mysigt,bra,fin,lmao,lol,cute', 'negative_reactions=ugh,fy,nej', 'reaction_weight_mod=1'])
        rf.write(''.join(lines))
    print('Please add token to configuration file.')
    sys.exit(0)


def signal_exit(signal, frame):
    sys.exit(0)

"""
Login when program is loaded.
"""
@client.event
async def on_ready():
    print('Logged in as: %s (%s)' % (client.user.name, client.user.id))
    signal.signal(signal.SIGINT, signal_exit)

"""
Print key and run.
"""
if data['debug']:
    print("Debugging.")
print('Token: ' + data['token'] + '\nKeychar: ' + data['key'])
client.run(data['token'])
