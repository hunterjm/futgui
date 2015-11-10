import time
from operator import itemgetter

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

def roundBid(bid):
    return int(increment(bid) * round(float(bid)/increment(bid)))

def bid(q, api, playerList, settings, trades={}):
    pileFull = False
    auctionsWon = 0
    bidDetails = {}

    api.resetSession()

    for item in playerList:
        bidDetails[item['player']['id']] = {
            'maxBid': item['buy'],
            'sell': item['sell'],
            'binPrice': item['bin']
            }

    for defId in bidDetails.keys():

        try:

            # Grab all items from tradepile
            tradepile = api.tradepile()
            # How many of this item do we already have listed?
            listed = sum([str(api.baseId(item['resourceId'])) == defId for item in tradepile])

            # Only bid if we don't already have a full trade pile and don't own too many of this player
            if not pileFull and api.credits > settings['minCredits'] and listed < settings['maxPlayer']:

                # Look for any BIN less than the BIN price
                for item in api.searchAuctions('player', defId=defId, max_buy=bidDetails[defId]['maxBid'], start=0, page_size=50):

                    # No Dups
                    if item['tradeId'] in trades:
                        continue

                    # Must have contract
                    if item['contract'] < 1:
                        continue

                    # Buy!!!
                    if api.bid(item['tradeId'], item['buyNowPrice']):
                        asset = api.cardInfo(item['resourceId'])
                        q.put('%s    Card Purchased: BIN %d on %s %s\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), item['buyNowPrice'], asset['Item']['FirstName'], asset['Item']['LastName']))
                        trades[item['tradeId']] = item['resourceId']
                    else:
                        q.put('%s    Bid Error: You are not allowed to bid on this trade\n' % (time.strftime('%Y-%m-%d %H:%M:%S')))


                # Search first 50 items in my price range to bid on within 5 minutes
                subtract = increment(bidDetails[defId]['maxBid'])
                for item in api.searchAuctions('player', defId=defId, max_price=bidDetails[defId]['maxBid']-subtract, start=0, page_size=50):

                    # Let's look at last 5 minutes for now
                    if item['expires'] > 600:
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
                        q.put('%s    New Bid: %d on %s %s\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), bid, asset['Item']['FirstName'], asset['Item']['LastName']))
                        trades[item['tradeId']] = item['resourceId']
                    else:
                        q.put('%s    Bid Error: You are not allowed to bid on this trade\n' % (time.strftime('%Y-%m-%d %H:%M:%S')))


            # Update watched items
            # q.put('%s    Updating watched items...\n' % (time.strftime('%Y-%m-%d %H:%M:%S')))
            for item in api.watchlist():
                baseId = str(api.baseId(item['resourceId']))
                maxBid = bidDetails[baseId]['maxBid']
                sell = bidDetails[baseId]['sell']
                binPrice = bidDetails[baseId]['binPrice']
                # How many of this item do we already have listed?
                listed = sum([str(api.baseId(item['resourceId'])) == baseId for item in tradepile])

                # Break if we don't have enough credits
                if api.credits < settings['minCredits']:
                    break

                # Continue if we already have too many listed
                if listed >= settings['maxPlayer']:
                    continue

                tradeId = item['tradeId']
                asset = api.cardInfo(trades[tradeId])

                # Handle Expired Items
                if item['expires'] == -1:

                    if (item['bidState'] == 'highest' or (item['tradeState'] == 'closed' and item['bidState'] == 'buyNow')):

                        # We won! Send to Pile!
                        q.put('%s    Auction Won: %d on %s %s\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), item['currentBid'], asset['Item']['FirstName'], asset['Item']['LastName']))
                        if api.sendToTradepile(tradeId, item['id'], safe=True):
                            # List on market
                            if api.sell(item['id'], sell, binPrice):
                                auctionsWon += 1
                                q.put('%s    Item Listed: %s %s for %d (%d BIN)\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), asset['Item']['FirstName'], asset['Item']['LastName'], sell, binPrice))
                            pileFull = False

                        else:
                            pileFull = True

                    else:

                        if api.watchlistDelete(tradeId):

                            if item['currentBid'] < maxBid:
                                q.put('%s    TOO SLOW: %s %s went for %d\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), asset['Item']['FirstName'], asset['Item']['LastName'], item['currentBid']))
                            else:
                                q.put('%s    Auction Lost: %s %s went for %d\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), asset['Item']['FirstName'], asset['Item']['LastName'], item['currentBid']))


                    # No need to keep track of expired bids
                    del trades[tradeId]

                elif item['bidState'] != 'highest':

                    # We were outbid
                    newBid = item['currentBid'] + increment(item['currentBid'])
                    if newBid > maxBid:
                        if api.watchlistDelete(tradeId):
                            q.put('%s    Outbid: Won\'t pay %d for %s %s\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), newBid, asset['Item']['FirstName'], asset['Item']['LastName']))
                            del trades[tradeId]

                    else:
                        if api.bid(tradeId, newBid):
                            q.put('%s    Bidding War: %d on %s %s\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), newBid, asset['Item']['FirstName'], asset['Item']['LastName']))
                        else:
                            q.put('%s    Bid Error: You are not allowed to bid on this trade\n' % (time.strftime('%Y-%m-%d %H:%M:%S')))

            # buy now goes directly to unassigned now
            for item in api.unassigned():
                maxBid = bidDetails[str(api.baseId(item['resourceId']))]['maxBid']
                sell = bidDetails[str(api.baseId(item['resourceId']))]['sell']
                binPrice = bidDetails[str(api.baseId(item['resourceId']))]['binPrice']

                tradeId = item['tradeId'] if item['tradeId'] is not None else -1
                asset = api.cardInfo(item['resourceId'])

                # We won! Send to Pile!
                q.put('%s    Auction Won: %d on %s %s\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), item['lastSalePrice'], asset['Item']['FirstName'], asset['Item']['LastName']))
                if api.sendToTradepile(tradeId, item['id'], safe=True):
                    # List on market
                    if api.sell(item['id'], sell, binPrice):
                        auctionsWon += 1
                        q.put('%s    Item Listed: %s %s for %d (%d BIN)\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), asset['Item']['FirstName'], asset['Item']['LastName'], sell, binPrice))
                    pileFull = False

                else:
                    pileFull = True

                # No need to keep track of expired bids
                if tradeId > 0:
                    del trades[tradeId]


            try:
                # Clean up Trade Pile & relist items
                sold = api.relist(clean=True)
                if sold:
                    q.put('%s    Trade Status: %d items sold\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), sold))
                    pileFull = False
            except InternalServerError:
                # auto re-list is down.  We have to do this manually...
                sold = 0
                completedTrades = sum([i['tradeState'] in ('expired', 'closed') for i in tradepile])
                if completedTrades > 0:
                    q.put('%s    Manually re-listing %d players.\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), completedTrades))
                    for i in tradepile:
                        sell = bidDetails[str(api.baseId(i['resourceId']))]['sell']
                        binPrice = bidDetails[str(api.baseId(i['resourceId']))]['binPrice']
                        if i['tradeState'] == 'closed':
                            api.tradepileDelete(i['tradeId'])
                            sold += 1
                        if i['tradeState'] == 'expired' and sell and binPrice:
                            api.sell(i['id'], sell, binPrice)

                pass

            if pileFull:

                # No use in trying more until min trade is done
                selling = api.tradepile()
                selling = sorted(selling, key=itemgetter('expires'), reverse=True)

                q.put('%s    Trade Pile Full! Resume bidding in %d seconds\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), selling[0]['expires']))
                time.sleep(selling[0]['expires'])

            q.put((auctionsWon, sold))
            auctionsWon = 0

        except (FutError, RequestException) as e:
            q.put(e)

from fut.exceptions import FutError, InternalServerError
from requests.exceptions import RequestException
