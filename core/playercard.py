import json, requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

def create(player, cards=None, cardinfo=None):

    cards = cards
    cardinfo = cardinfo
    _font25 = ImageFont.truetype('fonts/OpenSans-ExtraBold.ttf', 25)
    _font20b = ImageFont.truetype('fonts/OpenSans-Bold.ttf', 20)
    _font16 = ImageFont.truetype('fonts/OpenSans-ExtraBold.ttf', 16)
    _font16r = ImageFont.truetype('fonts/OpenSans-Regular.ttf', 16)

    if cards is None:
        cards = {
            'group0': Image.open('images/cards/group0.png'),
            'group1': Image.open('images/cards/group1.png'),
            'group2': Image.open('images/cards/group2.png')
        }
    if cardinfo is None:
        with open('images/cards/cards_big.json', 'r') as f:
                cardinfo = json.load(f)

    # make card
    cardbg = cards[cardinfo[player['color']]['image']].crop((
        0,
        cardinfo[player['color']]['position'],
        cardinfo[player['color']]['width'],
        cardinfo[player['color']]['position'] + cardinfo[player['color']]['height']
        ))
    card = Image.new("RGB", cardbg.size, (29,147,171))
    card.paste(cardbg, cardbg)

    #headshot image
    if player['specialImages']['largeTOTWImgUrl'] is not None:
        r = requests.get(player['specialImages']['largeTOTWImgUrl'])
    else:
        r = requests.get(player['headshot']['largeImgUrl'])
    headshot = Image.open(BytesIO(r.content))
    card.paste(headshot, (cardinfo[player['color']]['width']-headshot.size[1]-3, 40), headshot)

    # Rating
    renderedSize = _font25.getsize(str(player['rating']))
    rating = Image.new('RGBA', renderedSize, (255,255,255,0))
    d = ImageDraw.Draw(rating)
    d.text((0,0), str(player['rating']), font=_font25, fill=(54,33,27,255))
    card.paste(rating, (45, 20), rating)

    # Position
    renderedSize = _font25.getsize(str(player['position']))
    position = Image.new('RGBA', renderedSize, (255,255,255,0))
    d = ImageDraw.Draw(position)
    d.text((0,0), str(player['position']), font=_font16, fill=(54,33,27,255))
    card.paste(position, (45, 50), position)

    # club image
    r = requests.get(player['club']['imageUrls']['normal']['large'])
    club = Image.open(BytesIO(r.content))
    card.paste(club, (38, 76), club)

    # nation image
    r = requests.get(player['nation']['imageUrls']['large'])
    nation = Image.open(BytesIO(r.content))
    card.paste(nation, (38, 123), nation)

    if player['color'][0:3] == 'tot':
        fillColor = (255,234,128,255)
    else:
        fillColor = (54,33,27,255)

    # player name
    displayName = player['commonName'] if player['commonName'] is not '' else player['lastName']
    renderedSize = _font16.getsize(displayName)
    name = Image.new('RGBA', renderedSize, (255,255,255,0))
    d = ImageDraw.Draw(name)
    d.text((0,0), displayName, font=_font16, fill=fillColor)
    card.paste(name, (int((card.size[0]-renderedSize[0])/2), 162), name)

    # attributes
    pos = [
        { "x": 65, "y": 188 },
        { "x": 65, "y": 213 },
        { "x": 65, "y": 238 },
        { "x": 130, "y": 188 },
        { "x": 130, "y": 213 },
        { "x": 130, "y": 238 },
    ]
    count = 0;
    for attr in player['attributes']:

        value = str(attr['value'])
        renderedSize = _font16.getsize(value)
        img = Image.new('RGBA', renderedSize, (255,255,255,0))
        d = ImageDraw.Draw(img)
        d.text((0,0), value, font=_font16, fill=fillColor)
        card.paste(img, (pos[count]['x']-25, pos[count]['y']), img)

        name = attr['name'][-3:]
        renderedSize = _font16r.getsize(name)
        img = Image.new('RGBA', renderedSize, (255,255,255,0))
        d = ImageDraw.Draw(img)
        d.text((0,0), name, font=_font16r, fill=fillColor)
        card.paste(img, (pos[count]['x'], pos[count]['y']), img)
        count+=1

    # League
    renderedSize = _font20b.getsize(player['league']['abbrName'])
    league = Image.new('RGBA', renderedSize, (255,255,255,0))
    d = ImageDraw.Draw(league)
    d.text((0,0), player['league']['abbrName'], font=_font20b, fill=fillColor)
    card.paste(league, (int((card.size[0]-renderedSize[0])/2), 260), league)

    return card