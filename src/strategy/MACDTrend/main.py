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
        def __init__(self, strategy, symbol : str, fast : int, slow : int, signal : int, interval : Resolution):
            if fast >= slow:
                raise Exception(f"MACD fast[{fast}] >= slow[{slow}]")
            if signal >= fast:
                raise Exception(f"MACD signal[{signal}] >= fast[{fast}]")
            self.__tolerance = 0.0025
            self.__impl = strategy.MACD(symbol, fast, slow, signal, MovingAverageType.Exponential, interval)
        @property
        def IsReady(self) -> Boolean:
            return self.__impl.IsReady
        @property
        def Current(self):
            return self.__impl.Current
        @property
        def Slow(self):
            return self.__impl.Slow
        @property
        def Fast(self):
            return self.__impl.Fast
        @property
        def Signal(self):
            return self.__impl.Signal
        def decide(self) -> int:
            if not self.IsReady:
                return 0
            signal = (self.Current.Value - self.Signal.Current.Value)/self.Fast.Current.Value
            if signal > self.__tolerance:
                return 1
            elif signal < -self.__tolerance:
                return -1
            return 0

    def GetParamOrDefault(self, name : str, defaultValue : str = None) -> str:
        value = self.GetParameter(name)
        return value if value else defaultValue

    def AddMACDIndicator(self, symbol : str, fast : int, slow : int, signal : int, interval : Resolution) -> None:
        if symbol not in self.indicators:
            self.AddEquity(symbol, interval)
            self.stopMarketTicket[symbol] = None
            self.indicators[symbol] = {}
        symbolIndicators = self.indicators[symbol]
        if "MACD" in symbolIndicators:
            raise Exception(f"MACD is already registered for symbol {symbol}")
        symbolIndicators["MACD"] = self.MACDIndicator(self, symbol, fast, slow, signal, interval)

    def Initialize_Orig(self):
        self.SetStartDate(2019, 1, 1)
        self.SetEndDate(2021, 1, 1)
        #Search symbols in https://www.quantconnect.com/data
        symbols = sorted(set(["AAPL", "BABA", "TSLA", "INTC", "NVDA", "MU"]))
        self.maxSymbolAllocatedCount = int(self.GetParamOrDefault("max-symbol-allocated-count", defaultValue="3"))
        if self.maxSymbolAllocatedCount < 1 or self.maxSymbolAllocatedCount > len(symbols):
            raise Exception(f"Invalid max-symbol-allocated-count parameter value : {self.maxSymbolAllocatedCount}. Must be in the range[1, len(symbols)]")

        '''
        self.Schedule.On(
            self.DateRules.EveryDay("SPY"),
            self.TimeRules.AfterMarketOpen("SPY", 20),
            Action(self.AllocatePortfolio))
        '''
        
        for symbol in symbols:
            self.AddEquity(symbol, Resolution.Daily)
            self.indicators[symbol] = {"MACD": self.MACDIndicator(self, symbol, 7, 13, 3, Resolution.Daily)}
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

    def Initialize_Opt_2019_2021(self):
        self.SetStartDate(2019, 1, 1)
        self.SetEndDate(2021, 1, 1)

        interval = Resolution.Daily
        self.AddMACDIndicator("AAPL", 10, 14, 7, interval) #Total Trades: 11, Compounding Annual Return: 265.239, Sharpe Ratio: 2.899
        self.AddMACDIndicator("AMZN", 13, 15, 4, interval) #Total Trades: 5, Compounding Annual Return: 296.728, Sharpe Ratio: 5.514
        self.AddMACDIndicator("BAC", 9, 11, 3, interval) #Total Trades: 4, Compounding Annual Return: 73.923, Sharpe Ratio: 2.489
        #self.AddMACDIndicator("CSCO", 6, 15, 4, interval) #Total Trades: 44, Compounding Annual Return: 55.613, Sharpe Ratio: 1.72
        #self.AddMACDIndicator("F", 8, 10, 3, interval) #Total Trades: 2, Compounding Annual Return: 31.223, Sharpe Ratio: 1.535
        self.AddMACDIndicator("GE", 10, 12, 3, interval) #Total Trades: 3, Compounding Annual Return: 95.471, Sharpe Ratio: 2.236
        #self.AddMACDIndicator("GOOG", 7, 12, 4, interval) #Total Trades: 15, Compounding Annual Return: 34.081, Sharpe Ratio: 1.703
        #self.AddMACDIndicator("HP", 9, 12, 6, interval) #Total Trades: 5, Compounding Annual Return: 41.689, Sharpe Ratio: 1.82
        self.AddMACDIndicator("PYPL", 12, 15, 5, interval) #Total Trades: 10, Compounding Annual Return: 83.526, Sharpe Ratio: 2.17
        #self.AddMACDIndicator("T", 11, 15, 9, interval) #Total Trades: 6, Compounding Annual Return: 22.325, Sharpe Ratio: 1.601
        self.AddMACDIndicator("TSLA", 8, 16, 5, interval) #Total Trades: 9, Compounding Annual Return: 23.22, Sharpe Ratio: 1.757
        self.AddMACDIndicator("UPS", 10, 13, 7, interval) #Total Trades: 6, Compounding Annual Return: 42.712, Sharpe Ratio: 1.972

        self.maxSymbolAllocatedCount = int(self.GetParamOrDefault("max-symbol-allocated-count", defaultValue="3"))
        if self.maxSymbolAllocatedCount < 1 or self.maxSymbolAllocatedCount > len(self.indicators):
            raise Exception(f"Invalid max-symbol-allocated-count parameter value : {self.maxSymbolAllocatedCount}. Must be in the range[1, len(self.indicators)]")

    def Initialize_Opt_2016_2017(self):
        self.SetStartDate(2016, 1, 1)
        self.SetEndDate(2017, 1, 1)

        interval = Resolution.Daily
        self.AddMACDIndicator("AAPL", 7, 15, 5, interval) #Total Trades: 11, Compounding Annual Return: 40.248, Sharpe Ratio: 2.801
        self.AddMACDIndicator("AMD", 11, 14, 8, interval) #Total Trades: 2, Compounding Annual Return: 55.964, Sharpe Ratio: 2.501
        self.AddMACDIndicator("AMZN", 11, 26, 8, interval) #Total Trades: 11, Compounding Annual Return: 66.646, Sharpe Ratio: 2.928
        self.AddMACDIndicator("BAC", 9, 11, 3, interval) #Total Trades: 1, Compounding Annual Return: 258.374, Sharpe Ratio: 6.693
        self.AddMACDIndicator("CSCO", 11, 13, 4, interval) #Total Trades: 1, Compounding Annual Return: 95.573, Sharpe Ratio: 2.568
        self.AddMACDIndicator("GE", 10, 12, 4, interval) #Total Trades: 3, Compounding Annual Return: 404.598, Sharpe Ratio: 7.106
        self.AddMACDIndicator("GOOG", 12, 16, 9, interval) #Total Trades: 5, Compounding Annual Return: 48.918, Sharpe Ratio: 2.643
        self.AddMACDIndicator("INTC", 8, 12, 6, interval) #Total Trades: 14, Compounding Annual Return: 77.774, Sharpe Ratio: 2.721
        self.AddMACDIndicator("KO", 12, 27, 10, interval) #Total Trades: 5, Compounding Annual Return: 22.761, Sharpe Ratio: 2.2
        self.AddMACDIndicator("NVDA", 8, 15, 6, interval) #Total Trades: 5, Compounding Annual Return: 31.906, Sharpe Ratio: 2.865
        self.AddMACDIndicator("PEP", 13, 16, 8, interval) #Total Trades: 4, Compounding Annual Return: 87.065, Sharpe Ratio: 4.272
        self.AddMACDIndicator("PG", 8, 20, 6, interval) #Total Trades: 9, Compounding Annual Return: 31.405, Sharpe Ratio: 2.337
        self.AddMACDIndicator("UPS", 6, 11, 4, interval) #Total Trades: 2, Compounding Annual Return: 31.573, Sharpe Ratio: 2.775

        self.maxSymbolAllocatedCount = int(self.GetParamOrDefault("max-symbol-allocated-count", defaultValue="3"))
        if self.maxSymbolAllocatedCount < 1 or self.maxSymbolAllocatedCount > len(self.indicators):
            raise Exception(f"Invalid max-symbol-allocated-count parameter value : {self.maxSymbolAllocatedCount}. Must be in the range[1, len(self.indicators)]")

    def InitializeCommonParams(self):
        self.SetCash(100000)
        self.indicators = {}
        self.portfolioAllocation = {}
        #...trailing stop loss
        self.stopMarketTicket = {}
        self.stopLossTolerance = 0.093
        #...indicator signals
        self.signals = {}
        self.minSignalLevel = 1
        #...just in case add SPY
        self.AddEquity("SPY", Resolution.Daily)

    def Initialize(self):
        self.InitializeCommonParams()
        #self.Initialize_Opt_2016_2017()
        self.Initialize_Opt_2019_2021()
        #self.Initialize_Orig()

    def OnData(self, data):
        self.signals = {}
        
        for symbol, indicators in self.indicators.items():
            self.UpdateStopLossOnPriceChange(data, symbol)
            
            self.signals[symbol] = 0.
            for name, indicator in indicators.items():
                if not indicator.IsReady:
                    continue
                self.signals[symbol] = self.signals[symbol] + indicator.decide()
                
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

        allocationTasks = []
        for symbol in self.portfolioAllocation:
            if symbol not in newPortfolioAllocation:
                allocationTasks.append((symbol, 0.))
                
        for symbol, amount in newPortfolioAllocation.items():
            if symbol not in self.portfolioAllocation:
                if (symbol, 0.) in allocationTasks:
                    raise Exception(f"Symbol {symbol} is already ordered for liquidation")
                allocationTasks.append((symbol, amount))

        self.portfolioAllocation = newPortfolioAllocation
        for (symbol, amount) in allocationTasks:
            self.ClearStopLoss(symbol)
            if amount == 0.:
                self.Liquidate(symbol)
            else:
                self.SetHoldings(symbol, amount)
