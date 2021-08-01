from clr import AddReference
AddReference("System")
AddReference("QuantConnect.Algorithm")
AddReference("QuantConnect.Indicators")
AddReference("QuantConnect.Common")

from System import *
from QuantConnect import *
from QuantConnect.Algorithm import *
from QuantConnect.Indicators import *
from AlgorithmImports import *
from datetime import datetime

class MACDTrend(QCAlgorithm):
    
    class MACDIndicator:
        def __init__(self, strat, symbol, fast, slow, signal):
            self.start = strat
            self.tolerance = 0.0025
            self.ind = strat.MACD(symbol, fast, slow, signal, MovingAverageType.Exponential, Resolution.Daily)
        
        @property
        def IsReady(self):
            return self.ind.IsReady
    
        def decide(self, data):
            if not self.IsReady:
                return 0
            signal = (self.ind.Current.Value - self.ind.Signal.Current.Value)/self.ind.Fast.Current.Value
            if signal > self.tolerance:
                return 1
            elif signal < -self.tolerance:
                return -1
            return 0

    
    def Initialize(self):
        self.SetStartDate(2019, 1, 1)
        self.SetEndDate(2021, 1, 1)
        self.SetCash(100000)
        self.indicators = {}
        self.portfolioAllocation = {}
        #...trailing stop loss
        self.stopMarketTicket = {}
        self.stopLossTolerance = 0.093
        #...indicator signals
        self.signals = {}
        self.maxSymbolAllocatedCount = 3
        self.minSignalLevel = 1

        #Search symbols in https://www.quantconnect.com/data
        self.AddEquity("SPY", Resolution.Daily)
        self.symbols = sorted(set(["AAPL", "BABA", "TSLA", "INTC", "NVDA", "MU"]))
        #self.symbols = sorted(set(["AAPL"]))

        '''
        self.Schedule.On(
            self.DateRules.EveryDay("SPY"),
            self.TimeRules.AfterMarketOpen("SPY", 20),
            Action(self.AllocatePortfolio))
        '''
        
        for symbol in self.symbols:
            self.AddEquity(symbol, Resolution.Daily)
            self.indicators[symbol] = {"MACD": self.MACDIndicator(self, symbol, 7, 13, 3)}
            self.stopMarketTicket[symbol] = None
        ##########################################
        #BUY SPY only : T=1, 56.593%, B=-0.225, SH=1.035
        ##########################################
        #MACD: start=2019.1.1, end=2020.1.1, fast=7, slow=13, signal=3, tolerance=0.0025
        #AAPL: T=5 , 84.773%, B=-0.069, SR=3.929
        #BABA: T=7 , 39.028%, B=0.061 , SR=1.994
        #ARKK: T=7 , 6.561% , B=-0.017, SR=0.415
        #FB  : T=  , 8.161% , B=0.23  , SR=0.431
        #GLD : T=  , 0        , B=    , SR=
        #SPY : T=  , 0        , B=    , SR=
        #WMT : T=3  , 10.256%, B=-0.037, SR=0.881
        #INTC: T=8 , 30.886%, B=0.032 , SR=1.598
        #AMD : T=17, 32.002%, B=-0.071, SR=1.157
        #AMZN: T=6 , 0.754% , B=-0.005, SR=0.113
        ##########################################
        #MACD + trailing StopLoss(0.093): start=2019.1.1, end=2020.1.1, fast=7, slow=13, signal=3, tolerance=0.0025
        #AAPL: T=5 , 81.737%, B=-0.07, SR=3.803
        #BABA: T=7 , 39.028%, B=0.61 , SR=1.994
        #FB  : T=11, 16.422%, B=0.064 , SR=0.998
        #AMZN: T=6,  -9.518%, B=-0.006, SR=-0.774
        #WMT : T=3 , 13.036%, B=-0.009, SR=1.15
        #INTC: T=8 , 28.575%, B=0.035 , SR=1.474
        #AMD : T=25, 2.632% , B=-0.123, SR=0.211
        #GOOG: T=2 , 7.715% , B=0.001 , SR=0.619
        #HP  : T=11, 7.262% , B=0.004 , SR=0.374
        #NOK : T=11,-31.726%, B=0.058 , SR=-0.84
        #F   : T=9 ,-12.00% , B=      , SR=
        #GE  : T=14, 15.820%, B=      , SR=0.671
        #BAC : T=7 , 35.347%, B=0.01  , SR=2.276
        #AAL : T=13, 18.526%, B=      , SR=0.891
        #T   : T=2 , 7/4%   , B=      , SR=
        #PFE : T=5 , 4.72%  , B=      , SR=
        #AMC : T=14,-16.821%, B=      , SR=
        #CSCO: T=7, -7.040% , B=      , SR=
        #UBER: T=15,-22.451%, B=      , SR=
        #KO  : T=0 , 0      , B=      , SR=
        #PINS:T=19 ,-37.822%, B=      , SR=
        #MU  : T=14, 47.488%, B=      , SR=1.529
        #PG  : T=2 , -0.101%, B=      , SR=
        #PEP : T=0 , 0      , B=      , SR=
        #BRK-B: T=0, 0      , B=      , SR=
        #UPS : T=8 ,-11.039%, B=      , SR=
        #NVDA: T=12, 41.160%, B=      , SR=1.559
        #PYPL: T=6 ,-10.732%, B=      , SR=
        


    def OnData(self, data):
        self.signals = {}
        
        for symbol, indicators in self.indicators.items():
            self.UpdateStopLossOnPriceChange(data, symbol)
            
            self.signals[symbol] = 0.
            for name, indicator in indicators.items():
                if not indicator.IsReady:
                    continue
                self.signals[symbol] = self.signals[symbol] + indicator.decide(data)
                
        self.AllocatePortfolio()

    def SetStopLostOnFill(self, orderEvent):
        if self.stopLossTolerance == 0.:
            return
        if orderEvent.Status == OrderStatus.Filled or orderEvent.Status == OrderStatus.PartiallyFilled:
            order = self.Transactions.GetOrderById(orderEvent.OrderId)
            symbol = orderEvent.Symbol.Value
            self.Debug(f"{symbol} Order Filled : {order}")
            position = self.Portfolio[symbol].Quantity
            if position != 0:
                fillPrice = orderEvent.FillPrice
                if position > 0:
                    stopPrice = fillPrice * (1 - self.stopLossTolerance)
                else:
                    stopPrice = fillPrice * (1 + self.stopLossTolerance)
                self.Debug(f"{symbol} Set StopLoss: {-position}@{stopPrice}")
                self.stopMarketTicket[symbol] = self.StopMarketOrder(symbol, -position, stopPrice)
            else:
                self.Debug(f"{symbol} Clean allocation")
                if symbol in self.portfolioAllocation:
                    del self.portfolioAllocation[symbol]


    def OnOrderEvent(self, orderEvent):
        self.SetStopLostOnFill(orderEvent)

    def UpdateStopLossOnPriceChange(self, data, symbol):
        if self.stopLossTolerance == 0. or symbol not in data:
            return
        symbolData = data[symbol]
        if symbolData == None:
            return
        
        position = self.Portfolio[symbol].Quantity
        stopLoss = self.stopMarketTicket[symbol]
        if stopLoss and position != 0:
            stopPrice = stopLoss.Get(OrderField.StopPrice)
            currentPrice = symbolData.Close
            isUpdateStopPrice = False
            if position > 0:
                newStopPrice = currentPrice * (1 - self.stopLossTolerance)
                isUpdateStopPrice = newStopPrice > stopPrice
            else:
                newStopPrice = currentPrice * (1 + self.stopLossTolerance)
                isUpdateStopPrice = newStopPrice < stopPrice
                
            if isUpdateStopPrice:
                updateSettings = UpdateOrderFields()
                updateSettings.StopPrice = newStopPrice
                updateSettings.Tag = f"Update StopLoss at {newStopPrice}"
                stopLoss.Update(updateSettings)
    
    def ClearStopLoss(self, symbol):
        if self.stopLossTolerance == 0.:
            return
        stopLoss = self.stopMarketTicket[symbol]
        if stopLoss:
            self.Debug(f"{symbol} Clear StopLoss")
            stopLoss.Cancel("Cancel Stale StopLoss")
            self.stopMarketTicket[symbol] = None
    

    def GetBuyCandidates(self):
        ordered = sorted(self.signals, key=self.signals.get, reverse=True)
        ordered = ordered[:self.maxSymbolAllocatedCount]
        selected = []
        for symbol in ordered:
          if self.signals[symbol] >= self.minSignalLevel:
            selected.append(symbol)
        return selected

    def GetSellCandidates(self):
        ordered = sorted(self.signals, key=self.signals.get)
        selected = []
        for symbol in ordered:
          if self.signals[symbol] <= -self.minSignalLevel:
            selected.append(symbol)
        return selected

    def AllocatePortfolio(self):
        buyCandidates = self.GetBuyCandidates()
        sellCandidates = self.GetSellCandidates()
        
        newPortfolioAllocation = self.portfolioAllocation.copy()
        for sellSymbol in sellCandidates:
            if sellSymbol in newPortfolioAllocation:
                del newPortfolioAllocation[sellSymbol]
        
        for buySymbol in buyCandidates:
            if len(newPortfolioAllocation) >= self.maxSymbolAllocatedCount:
                break;
            newPortfolioAllocation[buySymbol] = 1./self.maxSymbolAllocatedCount

        self.Debug(f"Allocate {newPortfolioAllocation}")

        for symbol in self.portfolioAllocation:
            if symbol not in newPortfolioAllocation:
                self.ClearStopLoss(symbol)
                self.Liquidate(symbol)
                
        for symbol, amount in newPortfolioAllocation.items():
            if symbol not in self.portfolioAllocation:
                self.ClearStopLoss(symbol)
                self.SetHoldings(symbol, amount)

        self.portfolioAllocation = newPortfolioAllocation
