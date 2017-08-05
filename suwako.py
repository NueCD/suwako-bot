import discord
import asyncio
import random
import os
from urllib.request import urlopen
from xml.etree import ElementTree
from random import randint

debug = 0

client = discord.Client()
token = ''
key = ''
url = 'http://gelbooru.com/index.php?page=dapi&s=post&q=index&tags='
current_tags = None
current_channel = None
positive_reactions = []

def sort_ratings(ratings):
    tags = []
    scores = []

    for r in ratings:
        a = r.split(': ')
        tags.append(a[0])
        scores.append(int(a[1]))

    tags = [i[0] for i in sorted(zip(tags, scores), key=lambda l: l[1], reverse=True)]
    scores = list(reversed(sorted(scores)))

    ratings = []
    for i in range(len(tags)):
        ratings.append(': '.join([tags[i], str(scores[i])]))

    return ratings

def get_ratings(user):
    try:
        ratings = None
        with open(''.join(['ratings/', user, '.txt'])) as rw:
            ratings = rw.readlines()

        return list(map(lambda s: s.strip('\n'), ratings))

    except FileNotFoundError:
        return []

def save_ratings(user, ratings):
    with open(''.join(['ratings/', user, '.txt']), 'w') as rw:
        rw.write('\n'.join(ratings))

def search(tags, message):
    attempts = 0
    while(attempts < 3):
        try:
            posts = ElementTree.fromstring(urlopen(''.join([url, tags])).read())
            post = posts[randint(0, len(posts))]
            current_tags = filter(lambda k: ':' not in k, filter(None, post.attrib['tags'].split(' ')))
            current_channel = message.channel
            post = ''.join(['http:', post.attrib['file_url']])
            attempts = 4

        except IndexError:
            attempts += 1
            post = 'Could not find any...'
            current_channel = None
            current_tags = None

    return post

try:
    with open('config.txt', 'r') as rw:
        try:
            data = rw.readlines()
            token = data[0].strip('\n')
            key = data[1].strip('\n')
            debug = data[2].strip('\n')
            positive_reactions = data[3].strip('\n').split(',')

        except:
            print('Error reading configuration.')
            exit()

except FileNotFoundError:
    with open('config.txt', 'w') as rf:
        lines = '\n'.join(['[token]', '$', '0', 'wow,wau,hett,hot,mysigt,bra,fin,lmao,lol,cute'])
        rf.write(''.join(lines))
    print('Please add token to configuration file.')
    exit()

if not os.path.exists('ratings'):
    os.makedirs('ratings')

print('Token: ' + token + '\nKeychar: ' + key)

@client.event
async def on_ready():
    print('Logged in as: %s (%s)' % (client.user.name, client.user.id))

@client.event
async def on_message(message):
    global current_channel
    global current_tags
    global save_counter
    """
    Just reply with Hello
    """
    if message.content.startswith(''.join([key, 'hi'])):
        await client.send_message(message.channel, ''.join(['Hello ', 
            message.author.mention]))

        """
        Return random gelbooru image
        """
    elif message.content.startswith(''.join([key, 'img'])):
        tags = message.content.split(' ')
        tags.pop(0)

        try:
            if not tags:
                for t in get_ratings(message.author.id)[:10]:
                    tags.append(t.split(': ')[0])
                tags = random.sample(set(tags), 3)

        except ValueError:
            pass

        tags = '+'.join(tags)

        post = search(tags, message)

        await client.send_message(message.channel, post)

        """
        Return safe gelbooru image
        """
    elif message.content.startswith(''.join([key, 'simg'])):
        tags = message.content.split(' ')
        tags.pop(0)

        try:
            if not tags:
                for t in get_ratings(message.author.id)[:10]:
                    tags.append(t.split(': ')[0])
                tags = random.sample(set(tags), 3)

        except ValueError:
            pass

        tags = '+'.join(tags)
        tags = '+'.join([tags, 'rating:safe'])

        post = search(tags, message)

        await client.send_message(message.channel, post)

        """
        Return explicit gelbooru image
        """
    elif message.content.startswith(''.join([key, 'eimg'])):
        tags = message.content.split(' ')
        tags.pop(0)

        try:
            if not tags:
                for t in get_ratings(message.author.id)[:10]:
                    tags.append(t.split(': ')[0])
                tags = random.sample(set(tags), 3)

        except ValueError:
            pass

        tags = '+'.join(tags)
        tags = '+'.join([tags, 'rating:explicit'])

        post = search(tags, message)

        await client.send_message(message.channel, post)

        """
        Print top 10 ratings
        """
    elif message.content.startswith(''.join([key, 'rating'])):
        ratings = get_ratings(message.author.id)[:10]
        if ratings:
            post = '```Your top ten tags are:\n    %s```' % '\n    '.join(ratings)
        else:
            post = "```You don't have any tag ratings yet.```"

        await client.send_message(message.channel, post)

        """
        Clear all ratings
        """
    elif message.content.startswith(''.join([key, 'reset_rating'])):
        try:
            os.remove(''.join(['ratings/', message.author.id, '.txt']))
            post = '```Ratings removed.```'

        except ValueError:
            post = "```You don't have any ratings yet.```"

        await client.send_message(message.channel, post)

        """
        Remove ratings
        """
    elif message.content.startswith(''.join([key, 'remove_rating'])):
        r_tags = message.content.split(' ')
        r_tags.pop(0)
        tags = []
        scores = []

        for r in get_ratings(message.author.id):
            a = r.split(': ')
            tags.append(a[0])
            scores.append(int(a[1]))

        for r in r_tags:
            for i in range(len(tags)):
                try:
                    if r == tags[i]:
                    
                        tags.pop(i)
                        scores.pop(i)
                except IndexError:
                    pass
        
        ratings = []
        for i in range(len(tags)):
            ratings.append(': '.join([tags[i], str(scores[i])]))

        save_ratings(message.author.id, sort_ratings(ratings))

        post = '```Updated.```'

        await client.send_message(message.channel, post)

        """
        Help prints all commands
        """
    elif message.content.startswith(''.join([key, 'help'])):
        await client.send_message(message.channel, '```%s```' % '\n'.join(['Commandlist:\n'
            '    $hi - Says hello back.',
            '    $img - Returns a gelbooru image based on ratings.',
            '        Three random tags in your top 10 list will be used.',
            '        Ratings are improved by giving reactions to images.',
            '    $img [tags] - Returns a gelbooru image with tags.',
            '    $simg - Works like $img but includes safe tag.',
            '    $eimg - Works like $img but includes explicit tag.',
            '    $rating - See your own tag ratings.',
            '    $remove_rating [tags] - Remove tags from rating list.',
            '    $reset_rating - Resets tag ratings.',
            '    $credits - Show program credits.']))

        """
        Show credits
        """
    elif message.content.startswith(''.join([key, 'help'])):
        await client.send_message(message.channel, '```%s```' % '\n'.join(['Credits:\n'
            '    Made by Nue-class Destroyer.',
            '    Thanks to the maker of discord.py and my friends for helping me make this bot!',
            '    Source: https://github.com/NueCD/suwako-bot']))

    elif message.channel == current_channel and current_tags != None and any(positive in message.content.lower() for positive in positive_reactions):
        tags = []
        scores = []

        for r in get_ratings(message.author.id):
            a = r.split(': ')
            tags.append(a[0])
            scores.append(int(a[1]))

        for t in current_tags:
            try:
                scores[tags.index(t)] += 1

            except ValueError:
                tags.append(t)
                scores.append(0)

        ratings = []
        for i in range(len(tags)):
            ratings.append(': '.join([tags[i], str(scores[i])]))

        save_ratings(message.author.id, sort_ratings(ratings))

client.run(token)