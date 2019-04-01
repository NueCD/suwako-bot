import os, re, sys, random, asyncio, discord, signal, traceback
from urllib.request import urlopen
from xml.etree import ElementTree
from random import randint
from pyquery import PyQuery
from datetime import datetime

client = discord.Client()
data = {}
tag_weight = {}
url = 'http://gelbooru.com/index.php?page=dapi&s=post&q=index&tags='
source = None
current_tags = []
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
        scores.append(int(a[1]))

    tags = [i[0] for i in sorted(zip(tags, scores), key=lambda l: l[1], reverse=True)]
    scores = list(reversed(sorted(scores)))

    ratings = []
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
def change_weight(current_tags, add):
    for t in current_tags:
        try:
            if add:
                tag_weight[t] += 1
            else:
                tag_weight[t] -= 1

        except KeyError:
            tag_weight[t] = 0

    with open('ratings/weights.txt', 'w') as rw:
        ratings = []
        for t in tag_weight.items():
            ratings.append(''.join([t[0], ':', str(t[1])]))
        rw.write('\n'.join(ratings))


"""
Increese ratings
"""
def change_ratings(current_tags, user, add):
    tags = []
    scores = []
    ratings = []

    for r in get_ratings(user):
        a = r.split(': ')
        tags.append(a[0])
        scores.append(int(a[1]))

    if data['debug']:
        print('%i/%i' % (len(current_tags), len(tags)))

    for t in current_tags:
        try:
            scores[tags.index(t)]
            if add == 1:
                if tag_weight[t] < 10:
                    scores[tags.index(t)] += 3
                else:
                    scores[tags.index(t)] += 1
            elif add == 2:
                scores[tags.index(t)] += 5
            else:
                scores[tags.index(t)] -= 2

        except ValueError:
            tags.append(t)
            scores.append(0)
            change_weight(current_tags, 1)

        except KeyError:
            pass

    if add == 1:
        if tag_weight[t] > 10:
            change_weight(current_tags, 1)
        elif add == 2:
            change_weight(current_tags, 1)
        else:
            change_weight(current_tags, 0)

    for i in range(len(tags)):
        ratings.append(': '.join([tags[i], str(scores[i])]))

    if data['debug']:
        print(len(ratings))

    save_ratings(user, sort_ratings(ratings))


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
        if 'trap' in tags and 'shimakaze' in tags:
            return 'Dra åt helvete!'

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
def compile_tags(tags, user):
    global latest_search

    try:
        if not tags:
            for t in get_ratings(user)[:20]:
                tags.append(t.split(': ')[0])
            tags = random.sample(set(tags), 3)
            for t in get_ratings(user)[-3:]:
                tags.append(''.join(['-', t.split(': ')[0]]))

    except ValueError:
        pass
    
    tags = '+'.join(tags)
    if data['debug']:
        print(tags)

    try:
        if latest_search.replace('+rating:explicit', '').replace('+rating:safe', '') == tags and '*' not in latest_search:
            if data['debug']:
                print("Repetetive search")
            change_ratings(tags.split('+'), user, 2)

    except AttributeError:
        pass

    return tags


"""
Search for tags
"""
def tag_search(tag):
    tags = []
    if tag.startswith("-"):
        return ['', tag]
    try:
        html = PyQuery(urlopen(''.join(["https://gelbooru.com/index.php?page=tags&s=list&tags=*", \
            tag, '*&sort=desc&order_by=index_count'])).read())
        
        for p in html('table.highlightable tr').items():
            tags.append(p('span').text())

        tags = tags[:10]
        if data['debug']:
            print(tags)

    except:
        if data['debug']:
            print("Error when searching for tag.")
        return ['', tag]

    return tags


"""
Get tag from cache or search
"""
def cache_or_search(tag):
    a = []
    if tag.startswith("-"):
        return tag

    try:
        with open('tag_cache.txt', 'r') as f:
            a = f.readlines()
            a = list(map(lambda s: s.strip('\n'), a))

    except FileNotFoundError:
        pass

    for l in a:
        if l.split(':')[0] == tag:
            return l.split(':')[1]

    if data['debug']:
        print('Searching: %s' % tag)
    r = tag_search(tag)[1]
    if r:
        with open('tag_cache.txt', 'w') as f:
            a.append(':'.join([tag, r]))
            f.write('\n'.join(a))
        return r
    else:
        return tag


"""
The function run when recieving a call from Discord.
"""
@client.event
async def on_message(message):
    global current_channel
    global current_tags
    global save_counter
    post = None

    t_now = datetime.now()
    
    """
    Just reply with Hello.
    """
    if message.content.startswith(''.join([data['key'], 'hi'])):
        post = ''.join(['Hello ', message.author.mention])

        """
        Do the latest search again
        """
    elif message.content.startswith(''.join([data['key'], 'more'])):
        change_ratings(current_tags + message.content.split(' ')[:-1], message.author.id, 1)
        post = search(latest_search, message)

        """
        Return source of last image.
        """
    elif message.content.startswith(''.join([data['key'], 'source'])):
        if source:
            post = source
        else:
            post = '```Source is empty.```'


        """
        Return safe gelbooru image.
        """
    elif message.content.startswith(''.join([data['key'], 'img'])):
        retry = 0
        while retry < 5:

            if not data['autosearch']:
                tags = compile_tags(message.content.split(' ')[:-1], message.author.id)
                post = search('+'.join([tags, 'rating:safe']), message)
            else:
                tags = message.content.split(' ')
                tags.pop(0)

                t = []
                for a in tags:
                    t.append(cache_or_search(a))

                if data['debug']:
                    print(t)

                tags = compile_tags(t, message.author.id)
                post = search('+'.join([tags, 'rating:safe']), message)

            if post:
                retry = 6
            else:
                retry += 1

            if not post:
                post = '```Could not find anything using tags:\n    %s```' % ', '.join(tags.split('+'))

        """
        Return explicit gelbooru image.
        """
    elif message.content.startswith(''.join([data['key'], 'eimg'])):
        retry = 0
        while retry < 5:

            if not data['autosearch']:
                tags = compile_tags(message.content.split(' ')[:-1], message.author.id)
                post = search('+'.join([tags, 'rating:explicit']), message)
            else:
                tags = message.content.split(' ')
                tags.pop(0)

                t = []
                for a in tags:
                    t.append(cache_or_search(a))

                if data['debug']:
                    print(t)

                tags = compile_tags(t, message.author.id)
                post = search('+'.join([tags, 'rating:explicit']), message)

            if post:
                retry = 6
            else:
                if data['debug']:
                    print('Retry %i' % retry)
                retry += 1

            if not post:
                post = '```Could not find anything using tags:\n    %s```' % ', '.join(tags.split('+'))


        """
        Print top 10 ratings.
        """
    elif message.content.startswith(''.join([data['key'], 'rating'])):
        ratings = get_ratings(message.author.id)[:10]
        if ratings:
            post = '```Your top ten tags are:\n    %s```' % '\n    '.join(ratings)
        else:
            post = "```You don't have any tag ratings yet.```"

        """
        Clear all ratings.
        """
    elif message.content.startswith(''.join([data['key'], 'reset_rating'])):
        try:
            os.remove(''.join(['ratings/', message.author.id, '.txt']))
            post = '```Ratings removed.```'

        except ValueError:
            post = "```You don't have any ratings yet.```"

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

        """
        Get wildcard alternatives
        """
    elif message.content.startswith(''.join([data['key'], 'search'])):
        tags = tag_search(message.content.split(' ')[1])

        if tags:
            post = "```Tag matches (max 10):%s```" % '\n    '.join(tags)
        else:
            post = "```No matches found.```"

        """
        Help prints all commands.
        """
    elif message.content.startswith(''.join([data['key'], 'help'])):
        post = '```%s```' % '\n'.join([
            'Autosearch is set to %s.' % data['autosearch'],
            'Timed is set to %s' % data['timed'],
            '',
            'Commandlist:',
            '    %shi - Says hello back.' % data['key'],
            '    %simg [tags] - Returns a safe gelbooru image with tags.' % data['key'],
            '    %seimg [tags] - Returns an explicit  gelbooru image with tags.' % data['key'],
            '    %smore - Do the same search again.' % data['key'],
            '    %ssource - Returns source of previous image.' % data['key'],
            '    %srating - See your own tag ratings.' % data['key'],
            '    %ssearch [tag] - search for a tag.' % data['key'],
            '    %sremove_rating [tags] - Remove tags from rating list.' % data['key'],
            '    %sreset_rating - Resets tag ratings.' % data['key'],
            '    %scredits - Show program credits.' % data['key']])

        """
        Show credits.
        """
    elif message.content.startswith(''.join([data['key'], 'credits'])):
        post = '```%s```' % '\n'.join(['Credits:\n'
            '    Made by Nuekaze.',
            '    Thanks to the maker of discord.py and my friends for helping me make this bot!',
            '    Source: https://github.com/NueCD/suwako-bot'])

        """
        Look for positive responses to increese ratings.
        """
    elif message.channel == current_channel and current_tags != None and \
        any(positive in message.content.lower() for positive in data['positive_reactions']):
        if data['debug']:
            print("Positive word")

        change_ratings(current_tags, message.author.id, 1)

    elif message.channel == current_channel and current_tags != None and \
        any(negative in message.content.lower() for negative in data['negative_reactions']):
        if data['debug']:
            print("Negative word")
        
        change_ratings(current_tags, message.author.id, 0)

    if post:
        if data['timed']:
            t_measured = datetime.now() - t_now
            await client.send_message(message.channel, "%s\n%s" % (t_measured, post))
        else:
            await client.send_message(message.channel, post)

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

            if not os.path.exists('ratings'):
                os.makedirs('ratings')

            try:
                ratings = None
                with open('ratings/weights.txt', 'r') as rw:
                    for a in rw.read().split('\n'):
                        a = a.split(':')
                        tag_weight[a[0]] = int(a[1])

            except IndexError:
                pass
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
            'positive_reactions=wow,wau,hett,hot,mysigt,bra,fin,lmao,lol,cute', 'negative_reactions=ugh,fy,nej,wtf', 'reaction_weight_mod=1'])
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
