from utils.constants import SHARES_PER_CONTRACT, COMMISSION_PER_SHARE
from utils.helpers import makeOptionDateStr, cmp
from actions.login import *

def coveredCall(asset, buy, expiry, strike, contracts=1):
    contractAdjustment = SHARES_PER_CONTRACT * contracts
    optionDateStr = makeOptionDateStr(expiry)
    # get list of call options at given expiry and strike
    call = t.get_option_chain(asset).json()['callExpDateMap'][optionDateStr][str(strike)][0]
    lastPrice = t.get_quote(asset).json()[asset]['lastPrice']
    netPremium = call['bid']
    breakeven = buy - netPremium + COMMISSION_PER_SHARE
    maxGain = (strike - breakeven) * contractAdjustment
    maxLoss = breakeven * contractAdjustment
    return (maxGain, maxLoss, breakeven)

def marriedPut(asset, buy, expiry, strike, contracts=1):
    contractAdjustment = SHARES_PER_CONTRACT * contracts
    optionDateStr = makeOptionDateStr(expiry)
    # get list of put options at given expiry and strike
    put = t.get_option_chain(asset).json()['putExpDateMap'][optionDateStr][str(strike)][0]
    lastPrice = t.get_quote(asset).json()[asset]['lastPrice']
    netPremium = put['ask'] * -1
    breakeven = buy - netPremium + COMMISSION_PER_SHARE
    currentPnl = (lastPrice - breakeven) * contractAdjustment
    maxLoss = (breakeven - strike) * contractAdjustment
    return (currentPnl, maxLoss, breakeven)

def ironCondor(asset, expiry, putBuy, putWrite, callWrite, callBuy, contracts=1):
    contractAdjustment = SHARES_PER_CONTRACT * contracts
    optionDateStr = makeOptionDateStr(expiry)
    optionsChain = t.get_option_chain(asset).json()
    # get call and put chains at given expiry
    putChain = optionsChain['putExpDateMap'][optionDateStr]
    callChain = optionsChain['callExpDateMap'][optionDateStr]
    # calculate premiums for all for options and net
    putBuyPremium = putChain[str(putBuy)][0]['ask']
    putWritePremium = putChain[str(putWrite)][0]['bid']
    callWritePremium = callChain[str(callWrite)][0]['bid']
    callBuyPremium = callChain[str(callBuy)][0]['ask']
    netPremium = -putBuyPremium + putWritePremium + callWritePremium - callBuyPremium
    # calculate low and high breakeven prices
    breakevenLow = putWrite - netPremium + COMMISSION_PER_SHARE
    breakevenHigh = callWrite + netPremium - COMMISSION_PER_SHARE
    breakeven = {'low': breakevenLow, 'high': breakevenHigh}
    # calculate max gain and max loss
    maxGain = (netPremium - COMMISSION_PER_SHARE) * contractAdjustment
    maxLossLow = (breakevenLow - putBuy) * contractAdjustment
    maxLossHigh = (callBuy - breakevenHigh) * contractAdjustment
    maxLoss = {'low': maxLossLow, 'high': maxLossHigh}
    return (maxGain, maxLoss, breakeven)

def strangleBuy(asset, expiry, putBuy, callBuy, contracts=1):
    contractAdjustment = SHARES_PER_CONTRACT * contracts
    optionDateStr = makeOptionDateStr(expiry)
    optionsChain = t.get_option_chain(asset).json()
    # calculate premiums for options and net
    putPremium = optionsChain['putExpDateMap'][optionDateStr][str(putBuy)][0]['ask']
    callPremium = optionsChain['callExpDateMap'][optionDateStr][str(callBuy)][0]['ask']
    premiumSpent = putPremium + callPremium
    # calculate low and high breakeven prices
    breakevenLow = putBuy - premiumSpent - COMMISSION_PER_SHARE
    breakevenHigh = callBuy + premiumSpent + COMMISSION_PER_SHARE
    breakeven = {'low': breakevenLow, 'high': breakevenHigh}
    # calculate max loss and current pnl based on last price of asset
    maxLoss = (premiumSpent + COMMISSION_PER_SHARE) * contractAdjustment
    lastPrice = t.get_quote(asset).json()[asset]['lastPrice']
    currentPnlTmp = breakevenLow - lastPrice if cmp(abs(lastPrice - breakevenLow), abs(lastPrice - breakevenHigh)) == -1 else lastPrice - breakevenHigh
    currentPnl = max(currentPnlTmp * contractAdjustment, maxLoss*-1)
    return (currentPnl, maxLoss, breakeven)
