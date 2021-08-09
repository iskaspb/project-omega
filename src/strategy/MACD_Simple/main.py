from clr import AddReference
AddReference("System")
AddReference("QuantConnect.Algorithm")
AddReference("QuantConnect.Indicators")
AddReference("QuantConnect.Common")

from System import *
from QuantConnect import *
from QuantConnect.Algorithm import *
from QuantConnect.Indicators import *
from datetime import datetime

class MACD_Simple(QCAlgorithm):

    def Initialize(self):
        '''Initialise the data and resolution required, as well as the cash and start-end dates for your algorithm. All algorithms must initialized.'''

        self.symbol = "AAPL"
        self.SetStartDate(2018, 1, 1)    #Set Start Date
        self.SetEndDate(2019, 1, 1)      #Set End Date
        self.SetCash(100000)             #Set Strategy Cash
        # Find more symbols here: http://quantconnect.com/data
        self.AddEquity(self.symbol, Resolution.Daily)

        # define our daily macd(12,26) with a 9 day signal
        self.__macd = self.MACD(self.symbol, 7, 13, 3, MovingAverageType.Exponential, Resolution.Daily)
        self.__tolerance = 0.0025
        #self.__previous = datetime.min
        self.PlotIndicator("MACD", True, self.__macd, self.__macd.Signal)
        self.PlotIndicator(self.symbol, self.__macd.Fast, self.__macd.Slow)


    def OnData(self, data):
        if not self.__macd.IsReady:
            return

        holdings = self.Portfolio[self.symbol].Quantity

        signalDeltaPercent = (self.__macd.Current.Value - self.__macd.Signal.Current.Value)/self.__macd.Fast.Current.Value

        # if our macd is greater than our signal, then let's go long
        if holdings <= 0 and signalDeltaPercent > self.__tolerance:
            self.SetHoldings(self.symbol, 1.0)
        # of our macd is less than our signal, then let's go short
        elif holdings >= 0 and signalDeltaPercent < -self.__tolerance:
            self.SetHoldings(self.symbol, -1.0)
