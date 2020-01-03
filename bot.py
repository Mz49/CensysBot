import discord
import requests
import asyncio
from json import dumps

api = 'https://censys.io/api/v1/'
uid = 'YYY'
secret = 'ZZZ'
auth = (uid,secret)

bot_key = 'XXX'

months = ['January','February','March','April','May','June','July','August','September','October','November','December']
# days = ['st','dn','rd']
def pretty_date(ugly):
    date,time = ugly.split(' ')
    year,month,day = date.split('-')

    time = ':'.join(time.split(':')[:2])
    if time.startswith('0'):
        time = time[1:]

    month = months[int(month)-1]
    day = str(int(day))
    if day.endswith('1'):
        day += 'st'
    elif day.endswith('2'):
        day += 'nd'
    elif day.endswith('3'):
        day += 'rd'
    else:
        day += 'th'

    return '{} {}, {} at {}'.format(month,day,year,time)

def extract_field(query,field,split=False):
    field += '='
    if field in query:
        page_index = query.index(field)
        end_page = query[page_index:].find(' ')
        if end_page < 0:
            end_page = len(query)
        fields = query[page_index:end_page][len(field):]

        if split:
            fields = fields.split(',')

        new_query = query[:page_index] + query[page_index+end_page:]
        return new_query, fields

    return query, None



# async def page_handler(bot,client,msg,reply):

#     botreq = await replychan.send(embed=pages[0])
#     await botreq.add_reaction('⬅')
#     await botreq.add_reaction('➡')
#     page = 0
#     selection = ''
#     res = ''
#     while res is not None:
#         if selection == '⬅':
#             page -= 1
#             if page < 0:
#                 page = 0
#             else:
#                 await botreq.edit(embed=pages[page])
#         elif selection == '➡':
#             page += 1
#             if page == len(pages):
#                 page -= 1
#             else:
#                 await botreq.edit(embed=pages[page])
#         try:
#             res = await client.wait_for('reaction_add',timeout=60)
#             if str(res[1]) == str(msg.author):
#                 selection = res[0].emoji
#         except asyncio.TimeoutError:
#             res = None






def failure(error):
    embed = discord.Embed()
    embed.title = 'Failure.'

    if 'status' in error:
        embed.set_author(name='{}.'.format(error['error_type'].title()))
        embed.description = error['error']
    else:
        embed.set_author(name='HTTP {}'.format(error['error_code']))
        embed.description = error['error'].title() + '.'

    return embed


# print(requests.get(api + '/data',auth=(uid,secret)).text)
class censys(discord.Client):

    async def on_ready(self):
        print('Logged in as {}'.format(self.user))

    async def on_message(self,msg):
        if not msg.content.startswith(self.pref): return
        if msg.channel.id != 661519994152026113: return
        if msg.author.bot: return
        args = msg.content[len(self.pref):].lower().split()
        
        actions = ['search','account','view','report','data']

        if args[0] not in actions:
            await msg.channel.send(embed=discord.Embed(description='**{}** is not a valid command.'.format(args[0])))
            return

        if args[0] == 'account':
            r = requests.get(api + args[0],auth=auth)
            if r.status_code != 200:
                await msg.channel.send(embed=failure(r.json()))
                return

            info = r.json()
            embed = discord.Embed()
            embed.title = 'Account Info'
            embed.add_field(inline=False,name='User',value=info['login'])
            embed.add_field(inline=False,name='Email',value=info['email'])
            embed.add_field(inline=False,name='Last Login',value=pretty_date(info['last_login']))
            embed.add_field(inline=False,name='Usage',value='{}/{}'.format(info['quota']['used'],info['quota']['allowance']))
            embed.add_field(inline=False,name='Usage Reset',value=pretty_date(info['quota']['resets_at']))

            await msg.channel.send(embed=embed)
            return

        if args[0] == 'search':
            if not len(args) > 2:
                await msg.channel.send(embed=discord.Embed(description='Invalid command use.'))
                return

            options = ['websites','certificates','ipv4']
            if args[1] not in options:
                await msg.channel.send(embed=discord.Embed(description='Not a valid search index.'))
                return

            query = ' '.join(args[2:])

            query,fields = extract_field(query,'fields',True)
            query,page = extract_field(query,'page')
            query = query.strip()

            data = {}
            if fields is not None:
                data['fields'] = fields
            if page is not None:
                data['page'] = page
            data['query'] = query

            if len(query) < 1:
                await msg.channel.send(embed=discord.Embed(description='Please provide a query.'))
                return

            r = requests.post(api + args[0] + '/' + args[1],auth=auth,data=dumps(data))
            if r.status_code != 200:
                await msg.channel.send(embed=failure(r.json()))
                return

            data = r.json()
            print(dumps(data,indent=2))
            embed = discord.Embed()

            embed.set_author(name='Search Results for: {}'.format(data['metadata']['query']))
            embed.set_footer(text='Item {} out of {}'.format(1,data['metadata']['count']))
            for i in data['results'][0].keys():
                # if i == 'ip':
                #     embed.add_field(key=i.upper(),value=data['results'][0][i])
                # elif i == 'protocols':
                #     embed.add_field(key=i.title(),value='\n'.join(data['results'][0][i]))
                # else:
                if type(data['results'][0][i]) is str:
                    embed.add_field(name=i.title(),value=data['results'][0][i])
                elif type(data['results'][0][i]) is list:
                    embed.add_field(name=i.title(),value='\n'.join(data['results'][0][i]))

            await msg.channel.send(embed=embed)
            return


        print(args)

bot = censys()
bot.pref = '='
bot.run(bot_key)
