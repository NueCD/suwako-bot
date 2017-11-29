import os, re, sys, random, asyncio, discord
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
latest_search = None
positive_reactions = []


"""
Sort ratings alfabetical
"""
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


def add_ratings(current_tags, user):
    tags = []
    scores = []
    ratings = []

    for r in get_ratings(user):
        a = r.split(': ')
        tags.append(a[0])
        scores.append(int(a[1]))

    for t in current_tags:
        try:
            scores[tags.index(t)] += 1

        except ValueError:
            tags.append(t)
            scores.append(0)

    for i in range(len(tags)):
        ratings.append(': '.join([tags[i], str(scores[i])]))

    return ratings

"""
Load ratings from profiles
"""
def get_ratings(user):
    try:
        ratings = None
        with open(''.join(['ratings/', user, '.txt'])) as rw:
            ratings = rw.readlines()

        return list(map(lambda s: s.strip('\n'), ratings))

    except FileNotFoundError:
        return []


"""
Save ratings to profiles
"""
def save_ratings(user, ratings):
    with open(''.join(['ratings/', user, '.txt']), 'w') as rw:
        rw.write('\n'.join(ratings))


"""
Search for image on Gelbooru
"""
def search(tags, message):
    global current_tags
    global current_channel
    global latest_search

    try:
        # No waifu gay shit allowed. :)
        shim = re.compile(r'^.*shimakaze.*$')
        tags = tags.split('+')
        
        for t in tags:
            if shim.search(t):
                tags.append('-trap')
                tags.append('-cosplay')

        tags = '+'.join(tags)
        posts = ElementTree.fromstring(urlopen(''.join([url, tags])).read())
        if posts.attrib['success'] == "false":
            return ''.join(["```Gelbooru says:\n    ", posts.attrib['reason'], "```"])
        if not posts:
            return None
        post = posts[randint(0, len(posts)-1)]
        current_tags = filter(lambda k: ':' not in k, filter(None, post.attrib['tags'].split(' ')))
        current_channel = message.channel

        # Gelboodu added some strange url that sometimes returns 404.
        post = re.sub(r'simg.\.', '', post.attrib['file_url'])
        if post:
            latest_search = tags
        return post

    except IndexError:
        if debug:
            print(res)
        return None


"""
Compile raw string of tags to search string
"""
def compile_tags(message, user):
    global latest_search
    tags = message.content.split(' ')
    tags.pop(0)

    try:
        if not tags:
            for t in get_ratings(user)[:20]:
                tags.append(t.split(': ')[0])
            tags = random.sample(set(tags), 3)

    except ValueError:
        pass

    tags = '+'.join(tags)

    if latest_search == tags:
        save_ratings(message.author.id, sort_ratings(add_ratings(tags.split('+'), user)))

    return tags


"""
The function run when recieving a call from Discord.
"""
@client.event
async def on_message(message):
    global current_channel
    global current_tags
    global save_counter
    
    """
    Just reply with Hello.
    """
    if message.content.startswith(''.join([key, 'hi'])):
        await client.send_message(message.channel, ''.join(['Hello ', 
            message.author.mention]))

        """
        Return random gelbooru image.
        """
    elif message.content.startswith(''.join([key, 'img'])):
        tags = compile_tags(message, message.author.id)
        post = search(tags, message)

        if not post:
            post = '```Could not find anything using tags:\n    %s```' % ', '.join(tags.split('+'))

        await client.send_message(message.channel, post)

        """
        Return safe gelbooru image.
        """
    elif message.content.startswith(''.join([key, 'simg'])):
        tags = compile_tags(message, message.author.id)
        tags = '+'.join([tags, 'rating:safe'])
        post = search(tags, message)

        if not post:
            post = '```Could not find anything using tags:\n    %s```' % ', '.join(tags.split('+'))

        await client.send_message(message.channel, post)

        """
        Return explicit gelbooru image.
        """
    elif message.content.startswith(''.join([key, 'eimg'])):
        tags = compile_tags(message, message.author.id)
        tags = '+'.join([tags, 'rating:explicit'])
        post = search(tags, message)

        if not post:
            post = '```Could not find anything using tags:\n    %s```' % ', '.join(tags.split('+'))

        await client.send_message(message.channel, post)

        """
        Print top 10 ratings.
        """
    elif message.content.startswith(''.join([key, 'rating'])):
        ratings = get_ratings(message.author.id)[:10]
        if ratings:
            post = '```Your top ten tags are:\n    %s```' % '\n    '.join(ratings)
        else:
            post = "```You don't have any tag ratings yet.```"

        await client.send_message(message.channel, post)

        """
        Clear all ratings.
        """
    elif message.content.startswith(''.join([key, 'reset_rating'])):
        try:
            os.remove(''.join(['ratings/', message.author.id, '.txt']))
            post = '```Ratings removed.```'

        except ValueError:
            post = "```You don't have any ratings yet.```"

        await client.send_message(message.channel, post)

        """
        Remove ratings.
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
        Help prints all commands.
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
        Show credits.
        """
    elif message.content.startswith(''.join([key, 'credits'])):
        await client.send_message(message.channel, '```%s```' % '\n'.join(['Credits:\n'
            '    Made by Nue-class Destroyer.',
            '    Thanks to the maker of discord.py and my friends for helping me make this bot!',
            '    Source: https://github.com/NueCD/suwako-bot']))

        """
        Look for positive responses to increese ratings.
        """
    elif message.channel == current_channel and current_tags != None and \
        any(positive in message.content.lower() for positive in positive_reactions):
        
        ratings = add_ratings(current_tags, message.author.id)
        save_ratings(message.author.id, sort_ratings(ratings))


"""
Load configuration.
"""
try:
    with open('config.txt', 'r') as rw:
        try:
            data = rw.readlines()
            token = data[0].strip('\n')
            key = data[1].strip('\n')
            debug = data[2].strip('\n')
            positive_reactions = data[3].strip('\n').split(',')

            if not os.path.exists('ratings'):
                os.makedirs('ratings')

        except:
            print('Error reading configuration.')
            exit()


    """
    Generate configuration file and ratings folder if not already existing.
    """
except FileNotFoundError:
    with open('config.txt', 'w') as rf:
        lines = '\n'.join(['[token]', '$', '0', 'wow,wau,hett,hot,mysigt,bra,fin,lmao,lol,cute'])
        rf.write(''.join(lines))
    print('Please add token to configuration file.')
    exit()


"""
Login when program is loaded.
"""
@client.event
async def on_ready():
    print('Logged in as: %s (%s)' % (client.user.name, client.user.id))


"""
Print key and run.
"""
if debug:
    print("Debugging.")
print('Token: ' + token + '\nKeychar: ' + key)
client.run(token)
