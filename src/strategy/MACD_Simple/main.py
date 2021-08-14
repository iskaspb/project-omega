from datetime import datetime
from clr import AddReference
AddReference("System")
AddReference("QuantConnect.Algorithm")
AddReference("QuantConnect.Indicators")
AddReference("QuantConnect.Common")
from System import *
from QuantConnect import *
from QuantConnect.Algorithm import *
from QuantConnect.Indicators import *

def GenerateMACDParams() -> list:
    # instead of standard macd(12,26) with a 9 day signal we try different values
    macdParams = [(12, 26, 9)]
    slowRange = range(10, 28)
    fastRange = range(5, 14)
    signalRange = range(3, 11)
    for slow in slowRange:
        for fast in fastRange:
            for signal in signalRange:
                if (signal+1) < fast and (fast+1) < slow and (slow/4) <= signal :
                    validParam = (fast, slow, signal)
                    if macdParams[0] != validParam:
                        macdParams.append(validParam)
    return macdParams

class MACD_Simple(QCAlgorithm):
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

    def InitMACDParams(self):
        self.macdParams = GenerateMACDParams()
        self.Debug(f"MACD parameters generated : {len(self.macdParams)}")

    def InitSymbol(self):
        symbols = ["AAPL", "BABA", "TSLA", "INTC", "NVDA", "MU", "FB", "WMT", "AMD", "AMZN", "GOOG", "HP", "GE", "F", "T",  "BAC", "CSCO", "KO", "PINS", "PG", "PEP", "UPS", "PYPL"]
        symbolIndex = int(self.GetParameter("symbol-index"))
        self.symbol = symbols[symbolIndex]
        self.Debug(f"Select symbols[{symbolIndex}] = {self.symbol}")

    def Initialize(self):
        self.InitMACDParams()
        self.InitSymbol()

        self.SetStartDate(2019, 1, 1)    #Set Start Date
        self.SetEndDate(2021, 1, 1)      #Set End Date
        self.SetCash(100000)             #Set Strategy Cash
        # Find more symbols here: http://quantconnect.com/data
        self.AddEquity(self.symbol, Resolution.Daily)

        macdParamIndex = int(self.GetParameter("macd-param-index"))
        macdParam = self.macdParams[macdParamIndex]
        self.Debug(f"macdParams[{macdParamIndex}]={macdParam}")

        self.macd = self.MACDIndicator(self, self.symbol, macdParam[0], macdParam[1], macdParam[2], Resolution.Daily)
        #self.PlotIndicator("MACD", True, self.macd, self.macd.Signal)
        #self.PlotIndicator(self.symbol, self.macd.Fast, self.macd.Slow)


    def OnData(self, data):
        if not self.macd.IsReady:
            return

        holdings = self.Portfolio[self.symbol].Quantity
        macdDecision = self.macd.decide()

        if macdDecision > 0:
            if holdings <= 0:
                self.SetHoldings(self.symbol, 1.0)
        elif macdDecision < 0:
            ''' This is short sell logic
            if holdings >= 0:
                self.SetHoldings(self.symbol, -1.0)
            '''
            if holdings > 0:
                self.Liquidate(self.symbol)


