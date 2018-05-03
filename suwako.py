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
current_tags = None
current_channel = None
latest_search = None


"""
Sort ratings alfabetical
"""
def sort_ratings(ratings):
    tags = []
    scores = []

    for r in ratings:
        a = r.split(': ')
        tags.append(a[0])
        scores.append(float(a[1]))

    tags = [i[0] for i in sorted(zip(tags, scores), key=lambda l: l[1], reverse=True)]
    scores = list(reversed(sorted(scores)))

    ratings = []
    for i in range(len(tags)):
        ratings.append(': '.join([tags[i], str(scores[i])]))

    return ratings

"""
Increese ratings
"""
def add_ratings(current_tags, user):
    tags = []
    scores = []
    ratings = []

    for r in get_ratings(user):
        a = r.split(': ')
        tags.append(a[0])
        scores.append(float(a[1]))

    for t in current_tags:
        try:
            scores[tags.index(t)] += 1 * (data['reaction_weight_mod'] / tag_weight[t])

        except ValueError:
            tags.append(t)
            scores.append(0)

    for i in range(len(tags)):
        ratings.append(': '.join([tags[i], str(scores[i])]))

    return ratings

"""
Decreese ratings
"""
def lower_ratings(current_tags, user):
    tags = []
    scores = []
    ratings = []

    for r in get_ratings(user):
        a = r.split(': ')
        tags.append(a[0])
        scores.append(float(a[1]))

    for t in current_tags:
        try:
            scores[tags.index(t)] -= -1 * (data['reaction_weight_mod'] / tag_weight[t])

            if scores[tags.index(t)] < 0:
                scores[tags.index(t)] = 0

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
    if data['debug']:
        print("Updated ratings")
    with open(''.join(['ratings/', user, '.txt']), 'w') as rw:
        rw.write('\n'.join(ratings))


"""
Add weight
"""
def add_weight(current_tags):
    for t in current_tags:
        try:
            tag_weight[t] += (data['reaction_weight_mod'] / tag_weight[t])

        except KeyError:
            tag_weight[t] = 1.0

    with open('ratings/weights.txt', 'w') as rw:
        ratings = []
        for t in tag_weight.items():
            ratings.append(''.join([t[0], ':', str(t[1])]))
        rw.write('\n'.join(ratings))
    if data['debug']:
        print('Added weight')

"""
Search for image on Gelbooru
"""
def search(tags, message):
    global current_tags
    global current_channel
    global latest_search
    global source

    try:
        tagsa = tags
        tags = tags.split('+')

        tags.append('-trap')
        tags.append('-futanari')
        tags.append('-loli')
        tags.append('-shota')

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
            return None

        post = posts[randint(0, len(posts)-1)]
        current_tags = list(filter(lambda k: ':' not in k, filter(None, post.attrib['tags'].split(' '))))
        current_channel = message.channel

        # Gelboodu added some strange url that sometimes returns 404.
        #post = re.sub(r'simg.\.', '', post.attrib['file_url'])
        source = post.attrib['source']
        post = post.attrib['file_url']

        if post and tags:
            latest_search = tagsa

        return post

    except IndexError as res:
        if data['debug']:
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
    if data['debug']:
        print(tags)

    try:
        if latest_search.replace('+rating:explicit', '').replace('+rating:safe', '') == tags and '*' not in latest_search:
            if data['debug']:
                print("Repetetive search")
            save_ratings(message.author.id, sort_ratings(add_ratings(tags.split('+'), user)))

    except AttributeError:
        pass

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
    if message.content.startswith(''.join([data['key'], 'hi'])):
        await client.send_message(message.channel, ''.join(['Hello ', 
            message.author.mention]))

    """
    Return source of last image.
    """
    if message.content.startswith(''.join([data['key'], 'source'])):
        if source:
            await client.send_message(message.channel, source)
        else:
            await client.send_message(message.channel, '```Source is empty.```')


        """
        Return safe gelbooru image.
        """
    elif message.content.startswith(''.join([data['key'], 'img'])):
        tags = compile_tags(message, message.author.id)
        tags = '+'.join([tags, 'rating:safe'])
        post = search(tags, message)

        i = 0
        while i < 3 and not post:
            tags = compile_tags(message, message.author.id)
            tags = '+'.join([tags, 'rating:safe'])
            post = search(tags, message)
            i += 1

        if not post:
            post = '```Could not find anything using tags:\n    %s```' % ', '.join(tags.split('+'))

        add_weight(current_tags)
        await client.send_message(message.channel, post)

        """
        Return explicit gelbooru image.
        """
    elif message.content.startswith(''.join([data['key'], 'eimg'])):
        tags = compile_tags(message, message.author.id)
        tags = '+'.join([tags, 'rating:explicit'])
        post = search(tags, message)

        i = 0
        while i < 3 and not post:
            tags = compile_tags(message, message.author.id)
            tags = '+'.join([tags, 'rating:explicit'])
            post = search(tags, message)
            i += 1

        if not post:
            post = '```Could not find anything using tags:\n    %s```' % ', '.join(tags.split('+'))

        add_weight(current_tags)
        await client.send_message(message.channel, post)

        """
        Print top 10 ratings.
        """
    elif message.content.startswith(''.join([data['key'], 'rating'])):
        ratings = get_ratings(message.author.id)[:10]
        if ratings:
            post = '```Your top ten tags are:\n    %s```' % '\n    '.join(ratings)
        else:
            post = "```You don't have any tag ratings yet.```"

        await client.send_message(message.channel, post)

        """
        Clear all ratings.
        """
    elif message.content.startswith(''.join([data['key'], 'reset_rating'])):
        try:
            os.remove(''.join(['ratings/', message.author.id, '.txt']))
            post = '```Ratings removed.```'

        except ValueError:
            post = "```You don't have any ratings yet.```"

        await client.send_message(message.channel, post)

        """
        Remove ratings.
        """
    elif message.content.startswith(''.join([data['key'], 'remove_rating'])):
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
        Get wildcard alternatives
        """
    elif message.content.startswith(''.join([data['key'], 'tag'])):
        tags = []
        try:
            html = PyQuery(urlopen(''.join(["https://gelbooru.com/index.php?page=tags&s=list&tags=*", \
                message.content.split(' ')[1], '*&sort=desc&order_by=index_count'])).read())
            
            for p in html('table.highlightable tr').items():
                tags.append(p('span').text())

            tags = tags[:10]

        except:
            post = "General exception."

        if tags:
            post = "```Tag matches (max 10):%s```" % '\n    '.join(tags)
        else:
            post = "```No matches found.```"

        await client.send_message(message.channel, post)

        """
        Help prints all commands.
        """
    elif message.content.startswith(''.join([data['key'], 'help'])):
        await client.send_message(message.channel, '```%s```' % '\n'.join(['Commandlist:\n'
            '    $hi - Says hello back.',
            '    $img [tags] - Returns a safe gelbooru image with tags.',
            '    $eimg [tags] - Returns an explicit  gelbooru image with tags.',
            '    $source - Returns source of previous image.',
            '    $rating - See your own tag ratings.',
            '    $tag [tag] - search for a tag.',
            '    $remove_rating [tags] - Remove tags from rating list.',
            '    $reset_rating - Resets tag ratings.',
            '    $credits - Show program credits.']))

        """
        Show credits.
        """
    elif message.content.startswith(''.join([data['key'], 'credits'])):
        await client.send_message(message.channel, '```%s```' % '\n'.join(['Credits:\n'
            '    Made by Nuekaze.',
            '    Thanks to the maker of discord.py and my friends for helping me make this bot!',
            '    Source: https://github.com/NueCD/suwako-bot']))

        """
        Look for positive responses to increese ratings.
        """
    elif message.channel == current_channel and current_tags != None and \
        any(positive in message.content.lower() for positive in data['positive_reactions']):
        if data['debug']:
            print("Positive word")

        ratings = add_ratings(current_tags, message.author.id)
        save_ratings(message.author.id, sort_ratings(ratings))

    elif message.channel == current_channel and current_tags != None and \
        any(negative in message.content.lower() for negative in data['negative_reactions']):
        if data['debug']:
            print("Negative word")
        
        ratings = lower_ratings(current_tags, message.author.id)
        save_ratings(message.author.id, sort_ratings(ratings))

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
            input('Press enter to exit.')
            sys.exit(0)


    """
    Generate configuration file and ratings folder if not already existing.
    """
except FileNotFoundError:
    with open('config.txt', 'w') as rf:
        lines = '\n'.join(['token=[token]', 'key=$', 'debug=0', \
            'positive_reactions=wow,wau,hett,hot,mysigt,bra,fin,lmao,lol,cute', 'negative_reactions=ugh,fy,nej'])
        rf.write(''.join(lines))
    print('Please add token to configuration file.')
    input('Press any key to exit.')
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
