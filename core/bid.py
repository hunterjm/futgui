import fut
import time

def bid(q, api, defId, maxBid, sell, binPrice=0, minCredits=1000, trades={}):
    pileFull = False

    # Only bid if we don't already have a full trade pile
    if not pileFull and api.credits > minCredits:

        # Look for any BIN 4600 or less and buy it
        # q.put('%s    Search BIN: Max price of %d for asset definition %d\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), maxBid, defId))
        for item in api.searchAuctions('player', defId=defId, max_buy=maxBid, start=0, page_size=50):

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


        # Search first 50 items in my price range to bid on within 5 minutes
        # q.put('%s    Search Normal: Max price of %d for asset %d\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), maxBid-100, defId))
        for item in api.searchAuctions('player', defId=defId, max_price=maxBid-100, start=0, page_size=50):

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
                bid = item['currentBid'] + 100
            else:
                bid = item['startingBid']

            # Bid!!!
            if api.bid(item['tradeId'], bid):
                asset = api.cardInfo(item['resourceId'])
                q.put('%s    New Bid: %d on %s %s\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), bid, asset['Item']['FirstName'], asset['Item']['LastName']))
                trades[item['tradeId']] = item['resourceId']


    # Update watched items
    # q.put('%s    Updating watched items...\n' % (time.strftime('%Y-%m-%d %H:%M:%S')))
    for item in api.watchlist():

        # Break if we don't have enough credits
        if api.credits < minCredits:
            break

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
            newBid = item['currentBid'] + 100
            if newBid > maxBid:
                if api.watchlistDelete(tradeId):
                    q.put('%s    Outbid: Won\'t pay %d for %s %s\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), newBid, asset['Item']['FirstName'], asset['Item']['LastName']))
                    del trades[tradeId]

            else:
                if api.bid(tradeId, newBid):
                    q.put('%s    Bidding War: %d on %s %s\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), newBid, asset['Item']['FirstName'], asset['Item']['LastName']))

    # buy now goes directly to unassigned now
    for item in api.unassigned():

        tradeId = item['tradeId'] if item['tradeId'] is not None else -1
        asset = api.cardInfo(item['resourceId'])

        # We won! Send to Pile!
        q.put('%s    Auction Won: %d on %s %s\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), item['lastSalePrice'], asset['Item']['FirstName'], asset['Item']['LastName']))
        if api.sendToTradepile(tradeId, item['id'], safe=True):
            # List on market
            if api.sell(item['id'], sell, binPrice):
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
        pass

    if pileFull:

        # No use in trying more until min trade is done
        selling = api.tradepile()
        selling = sorted(selling, key=itemgetter('expires'), reverse=True)

        q.put('%s    Trade Pile Full! Resume bidding in %d seconds\n' % (time.strftime('%Y-%m-%d %H:%M:%S'), selling[0]['expires']))
        time.sleep(selling[0]['expires'])

from fut.exceptions import InternalServerError
