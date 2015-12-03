import time

from operator import itemgetter
from frames.misc.auctions import Card, PlayerCard, EventType


def increment(bid):
    if bid < 1000:
        return 50
    elif bid < 10000:
        return 100
    elif bid < 50000:
        return 250
    elif bid < 100000:
        return 500
    else:
        return 1000

def decrement(bid):
    if bid <= 1000:
        return 50
    elif bid <= 10000:
        return 100
    elif bid <= 50000:
        return 250
    elif bid <= 100000:
        return 500
    else:
        return 1000

def roundBid(bid):
    return int(increment(bid) * round(float(bid)/increment(bid)))


def bid(q, api, playerList, settings):
    pileFull = False
    auctionsWon = 0
    bidDetails = {}
    trades = {}

    api.resetSession()

    for item in playerList:
        bidDetails[item['player']['id']] = {
            'maxBid': item['buy'],
            'sell': item['sell'],
            'binPrice': item['bin']
        }

    for item in api.watchlist():
        trades[item['tradeId']] = item['resourceId']

    # Grab all items from tradepile
    tradepile = api.tradepile()

    # Log selling players
    for trade in tradepile:
        asset = api.cardInfo(trade['resourceId'])
        if str(asset['Item']['ItemType']).startswith('Player'):
            displayName = asset['Item']['CommonName'] if asset['Item']['CommonName'] else asset['Item']['LastName']
        else:
            displayName = asset['Item']['Desc']
        card = PlayerCard(trade, displayName)
        q.put((card, EventType.SELLING, api.credits))

    for defId in bidDetails.keys():

        if bidDetails[defId]['maxBid'] < 100:
            continue

        try:

            # How many of this item do we already have listed?
            listed = sum([str(api.baseId(item['resourceId'])) == defId for item in tradepile])

            # Only bid if we don't already have a full trade pile and don't own too many of this player
            binWon = False
            if not pileFull and api.credits > settings['minCredits'] and listed < settings['maxPlayer']:

                # Look for any BIN less than the BIN price
                for item in api.searchAuctions('player', defId=defId, max_buy=bidDetails[defId]['maxBid'], start=0, page_size=50):
                    # player safety checks for every possible bid
                    if listed >= settings['maxPlayer'] or api.credits < settings['minCredits']:
                        break

                    # No Dups
                    if item['tradeId'] in trades:
                        continue

                    # Must have contract
                    if item['contract'] < 1:
                        continue

                    # Buy!!!
                    if api.bid(item['tradeId'], item['buyNowPrice']):
                        asset = api.cardInfo(item['resourceId'])
                        displayName = asset['Item']['CommonName'] if asset['Item']['CommonName'] else asset['Item']['LastName']
                        card = PlayerCard(item, displayName)

                        q.put((card, EventType.BIN, api.credits))
                        q.put('%s    Card Purchased: BIN %d on %s %s\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), item['buyNowPrice'], asset['Item']['FirstName'], asset['Item']['LastName']))
                        trades[item['tradeId']] = item['resourceId']
                        binWon = True
                        listed += 1
                    else:
                        q.put('%s    Bid Error: You are not allowed to bid on this trade\n' % (time.strftime('%Y-%m-%d %H:%M:%S')))

                # Search first 50 items in my price range to bid on within 5 minutes
                if not settings['snipeOnly']:
                    bidon = 0
                    subtract = decrement(bidDetails[defId]['maxBid'])
                    for item in api.searchAuctions('player', defId=defId, max_price=bidDetails[defId]['maxBid']-subtract, start=0, page_size=50):
                        # player safety checks for every possible bid
                        # Let's look at last 5 minutes for now and bid on 5 players max
                        if item['expires'] > 300 or bidon >= 5 or listed >= settings['maxPlayer'] or api.credits < settings['minCredits']:
                            break

                        # No Dups
                        if item['tradeId'] in trades:
                            continue

                        # Must have contract
                        if item['contract'] < 1:
                            continue

                        # Set my initial bid
                        if item['currentBid']:
                            bid = item['currentBid'] + increment(item['currentBid'])
                        else:
                            bid = item['startingBid']

                        # Bid!!!
                        if api.bid(item['tradeId'], bid):
                            asset = api.cardInfo(item['resourceId'])
                            displayName = asset['Item']['CommonName'] if asset['Item']['CommonName'] else asset['Item']['LastName']
                            card = PlayerCard(item, displayName)

                            card.currentBid = bid
                            q.put((card, EventType.NEWBID, api.credits))
                            q.put('%s    New Bid: %d on %s %s\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), bid, asset['Item']['FirstName'], asset['Item']['LastName']))
                            trades[item['tradeId']] = item['resourceId']
                            bidon += 1
                        else:
                            q.put('%s    Bid Error: You are not allowed to bid on this trade\n' % (time.strftime('%Y-%m-%d %H:%M:%S')))

            if not settings['snipeOnly'] and trades:
                # Update watched items
                q.put('%s    Updating watched items...\n' % (time.strftime('%Y-%m-%d %H:%M:%S')))
                for item in api.tradeStatus([tradeId for tradeId in trades]):
                    item['resourceId'] = trades[item['tradeId']]
                    baseId = str(abs(item['resourceId'] + 0x80000000))
                    if baseId not in bidDetails:
                        continue
                    maxBid = bidDetails[baseId]['maxBid']
                    sell = bidDetails[baseId]['sell']
                    binPrice = bidDetails[baseId]['binPrice']
                    # How many of this item do we already have listed?
                    listed = sum([str(api.baseId(trade['resourceId'])) == baseId for trade in tradepile])

                    tradeId = item['tradeId']
                    if tradeId not in trades:
                        continue

                    asset = api.cardInfo(trades[tradeId])
                    displayName = asset['Item']['CommonName'] if asset['Item']['CommonName'] else asset['Item']['LastName']
                    card = PlayerCard(item, displayName)

                    # Update the card, regardless what will happen
                    q.put((card, EventType.UPDATE, api.credits))

                    # Handle Expired Items
                    if item['expires'] == -1:
                        if (item['bidState'] == 'highest' or (item['tradeState'] == 'closed' and item['bidState'] == 'buyNow')):

                            # We won! Send to Pile!
                            q.put((card, EventType.BIDWON, api.credits))
                            q.put('%s    Auction Won: %d on %s %s\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), item['currentBid'], asset['Item']['FirstName'], asset['Item']['LastName']))
                            if api.sendToTradepile(tradeId, item['id'], safe=True):
                                # List on market
                                if api.sell(item['id'], sell, binPrice):
                                    auctionsWon += 1
                                    listed += 1
                                    # No need to keep track of expired bids
                                    del trades[tradeId]
                                    q.put('%s    Item Listed: %s %s for %d (%d BIN)\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), asset['Item']['FirstName'], asset['Item']['LastName'], sell, binPrice))
                                pileFull = False

                            else:
                                q.put('%s    Error: %s %s could not be placed in the tradepile...\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), asset['Item']['FirstName'], asset['Item']['LastName']))
                                pileFull = True

                        else:

                            if api.watchlistDelete(tradeId):

                                if item['currentBid'] < maxBid:
                                    q.put((card, EventType.LOST, api.credits))
                                    q.put('%s    TOO SLOW: %s %s went for %d\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), asset['Item']['FirstName'], asset['Item']['LastName'], item['currentBid']))
                                else:
                                    q.put((card, EventType.LOST, api.credits))
                                    q.put('%s    Auction Lost: %s %s went for %d\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), asset['Item']['FirstName'], asset['Item']['LastName'], item['currentBid']))

                                # No need to keep track of expired bids
                                del trades[tradeId]

                    elif item['bidState'] != 'highest':
                        # Continue if we already have too many listed or we don't have enough credits
                        if listed >= settings['maxPlayer'] or api.credits < settings['minCredits']:
                            continue

                        # We were outbid
                        newBid = item['currentBid'] + increment(item['currentBid'])
                        if newBid > maxBid:
                            if api.watchlistDelete(tradeId):
                                q.put((card, EventType.OUTBID, api.credits))
                                q.put('%s    Outbid: Won\'t pay %d for %s %s\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), newBid, asset['Item']['FirstName'], asset['Item']['LastName']))
                                del trades[tradeId]

                        else:
                            if api.bid(tradeId, newBid):
                                card.currentBid = newBid
                                q.put((card, EventType.BIDWAR, api.credits))
                                q.put('%s    Bidding War: %d on %s %s\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), newBid, asset['Item']['FirstName'], asset['Item']['LastName']))
                            else:
                                q.put('%s    Bid Error: You are not allowed to bid on this trade\n' % (time.strftime('%Y-%m-%d %H:%M:%S')))

            # buy now goes directly to unassigned now
            if binWon:
                for item in api.unassigned():
                    baseId = str(abs(item['resourceId'] + 0x80000000))
                    if baseId not in bidDetails:
                        continue
                    maxBid = bidDetails[baseId]['maxBid']
                    sell = bidDetails[baseId]['sell']
                    binPrice = bidDetails[baseId]['binPrice']

                    tradeId = item['tradeId'] if item['tradeId'] is not None else -1
                    asset = api.cardInfo(item['resourceId'])
                    displayName = asset['Item']['CommonName'] if asset['Item']['CommonName'] else asset['Item']['LastName']
                    card = PlayerCard(item, displayName)

                    # We won! Send to Pile!
                    q.put((card, EventType.BIDWON, api.credits))
                    q.put('%s    Auction Won: %d on %s %s\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), item['lastSalePrice'], asset['Item']['FirstName'], asset['Item']['LastName']))
                    if api.sendToTradepile(tradeId, item['id'], safe=True):
                        # List on market
                        if api.sell(item['id'], sell, binPrice):
                            auctionsWon += 1
                            # No need to keep track of expired bids
                            if tradeId > 0:
                                del trades[tradeId]
                            q.put('%s    Item Listed: %s %s for %d (%d BIN)\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), asset['Item']['FirstName'], asset['Item']['LastName'], sell, binPrice))
                        pileFull = False

                    else:
                        q.put('%s    Error: %s %s could not be placed in the tradepile...\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), asset['Item']['FirstName'], asset['Item']['LastName']))
                        pileFull = True

            # relist items
            expired = sum([i['tradeState'] == 'expired' for i in tradepile])
            if expired > 0:

                relistFailed = False
                if settings['relistAll']:
                    try:
                        api.relist()
                    except InternalServerError:
                        relistFailed = True
                        pass

                if not settings['relistAll'] or relistFailed:
                    q.put('%s    Manually re-listing %d players.\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), expired))
                    for i in tradepile:
                        baseId = str(abs(i['resourceId'] + 0x80000000))
                        if baseId in bidDetails:
                            sell = i['startingBid'] if settings['relistAll'] else bidDetails[baseId]['sell']
                            binPrice = i['buyNowPrice'] if settings['relistAll'] else bidDetails[baseId]['binPrice']
                            if i['tradeState'] == 'expired' and sell and binPrice:
                                api.sell(i['id'], sell, binPrice)

            # Log sold items
            sold = sum([i['tradeState'] == 'closed' for i in tradepile])
            if sold > 0:
                for i in tradepile:
                    if i['tradeState'] == 'closed':
                        asset = api.cardInfo(i['resourceId'])
                        displayName = asset['Item']['CommonName'] if asset['Item']['CommonName'] else asset['Item']['LastName']
                        card = PlayerCard(i, displayName)
                        q.put((card, EventType.SOLD, api.credits))
                        q.put('%s    Item Sold: %s %s for %d\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), asset['Item']['FirstName'], asset['Item']['LastName'], i['currentBid']))
                        api.tradepileDelete(i['tradeId'])
                        pileFull = False

            # Sleep if we have no more space left
            if pileFull:

                # Update tradepile and verify that we are really full and it just wasn't an error
                tradepile = api.tradepile()
                if len(tradepile) >= api.tradepile_size:
                    # No use in trying more until min trade is done
                    selling = sorted(tradepile, key=itemgetter('expires'), reverse=True)
                    q.put('%s    Trade Pile Full! Resume bidding in %d seconds\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), selling[0]['expires']))
                    time.sleep(selling[0]['expires'])

            q.put((auctionsWon, sold, api.credits))

            # re-sync tradepile if we won something
            if auctionsWon or expired or sold:
                tradepile = api.tradepile()

            # Reset auctions won
            auctionsWon = 0

        except (FutError, RequestException) as e:
            q.put(e)

    # update our api
    q.put(api)

from fut.exceptions import FutError, InternalServerError
from requests.exceptions import RequestException
