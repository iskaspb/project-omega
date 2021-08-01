class SPYRebalance(QCAlgorithm):

    def Initialize(self):
        self.SetStartDate(2019, 1, 1)
        self.SetEndDate(2021, 1, 1)
        self.initialCash = 100000
        self.SetCash(self.initialCash)
        ''' Allocation example from https://www.etf.com/sections/etf-strategist-corner/sector-sector-sp-500?nopaging=1
            Information Technology    27.6%    VGT    XLK
            Health Care               13.5%    VHT    XLV
            Consumer Discretionary    12.7%    VCR    XLY
            Communication Services    10.8%    VOX    XLC
            Financials                10.4%    VFH    XLF
            Industrials               8.4%     VIS    XLI
            Consumer Staples          6.5%     VDC    XLP
            Utilities                 2.8%     VPU    XLU
            Materials                 2.6%     VAW    XLB
            Real Estate               2.4%     VNQ    XLRE
            Energy                    2.3%     VDE    XLE        
            
            Vanguard Sector ETF:
            'VGT' : 0.276,
            'VHT' : 0.135,
            'VCR' : 0.127,
            'VOX' : 0.108,
            'VFH' : 0.104,
            'VIS' : 0.084,
            'VDC' : 0.065,
            'VPU' : 0.028,
            'VAW' : 0.026,
            'VNQ' : 0.024,
            'VDE' : 0.023,
            
            SPDR Sector ETF
            'XLK' : 0.276,
            'XLV' : 0.135,
            'XLY' : 0.127,
            'XLC' : 0.108,
            'XLF' : 0.104,
            'XLI' : 0.084,
            'XLP' : 0.065,
            'XLU' : 0.028,
            'XLB' : 0.026,
            'XLRE' : 0.024,
            'XLE' : 0.023,
        '''
        
        self.symbolWeights = {
            'VGT' : 0.276,
            'VHT' : 0.135,
            'VCR' : 0.127,
            'VOX' : 0.108,
            'VFH' : 0.104,
            'VIS' : 0.084,
            'VDC' : 0.065,
            'VPU' : 0.028,
            'VAW' : 0.026,
            'VNQ' : 0.024,
            'VDE' : 0.023,
        }
        
        self.AddEquity("SPY", Resolution.Daily)
        self.initialHolding = []
        for symbol, weight in self.symbolWeights.items():
            self.AddEquity(symbol, Resolution.Daily)
            self.initialHolding.append(PortfolioTarget(symbol, weight))

        ''' Example of different scheduling
        https://www.quantconnect.com/docs/v2/writing-algorithms/user-guides/algorithm-reference/scheduled-events
        https://www.quantconnect.com/docs/algorithm-reference/scheduled-events
        '''
        self.Schedule.On(
            self.DateRules.MonthStart("SPY"),
            self.TimeRules.AfterMarketOpen("SPY"),
            self.RebalancingCode)
        
        self.initialSPYPrice = 0
                         

    def OnData(self, data):
        self.Plot("Data Chart", "SPY", self.Securities["SPY"].Close)
        if self.initialSPYPrice == 0:
            self.initialSPYPrice = self.Securities["SPY"].Close
            
        self.Plot("Strategy Equity", "SPY", (self.initialCash / self.initialSPYPrice ) * self.Securities["SPY"].Close)

    def RebalancingCode(self):
        self.SetHoldings(self.initialHolding)
