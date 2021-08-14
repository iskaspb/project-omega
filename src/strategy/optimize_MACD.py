import subprocess
import re
from timeit import default_timer as timer
from datetime import timedelta

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


def main() -> None:
    start = timer()

    macdParams = GenerateMACDParams()
    #macdParams = macdParams[0:1]
    print(f"MACD parameters generated : {len(macdParams)}")
    symbols = sorted(set(["AAPL", "BABA", "TSLA", "INTC", "NVDA", "MU", "FB", "WMT", "AMD", "AMZN", "GOOG", "HP", "GE", "F", "T",  "BAC", "CSCO", "KO", "PINS", "PG", "PEP", "UPS", "PYPL"]))
    print(f"Optimize for {len(symbols)} symbols : {symbols}")

    for symbolIndex in range(0, len(symbols)-1):
        startOptimize = timer()

        symbol = symbols[symbolIndex]
        #optimizeCmd = ["lean", "optimize", "--strategy", 'Grid Search', "--target", 'Sharpe Ratio', "--target-direction", "max", "--parameter", "macd-param-index", "0", f"{len(macdParams)-1}", "1", "--parameter", "symbol-index", f"{symbolIndex}", f"{symbolIndex}", "1", "MACD_Simple"]
        optimizeCmd = ["lean", "optimize", "--strategy", "Grid Search", "--target", "Compounding Annual Return", "--target-direction", "max", "--constraint", "Sharpe Ratio >= 1.5", "--parameter", "macd-param-index", "0", f"{len(macdParams)-1}", "1", "--parameter", "symbol-index", f"{symbolIndex}", f"{symbolIndex}", "1", "MACD_Simple"]
        print(f"#optimize for symbol {symbol} : {' '.join(optimizeCmd)}", flush=True)
        process = subprocess.Popen(optimizeCmd, stdout=subprocess.PIPE)
        output, error = process.communicate()
        output = output.decode('utf-8', 'ignore')[-3000:]

        x = re.search(r"Optimization has ended. Result was not", output)
        if x:
            print(f"#Optimization of {symbol} failed, please review optimization criterias")
            print(output)
            continue

        x = re.search(r"Optimal parameters: symbol-index: (\d+), macd-param-index: (\d+)", output)
        if x:
            resultSymbolIndex = int(x.group(1))
            if symbolIndex != resultSymbolIndex:
                raise Exception(f"Wrong symbol index! Expecting {symbolIndex} however got {resultSymbolIndex}")
            resultMACDParamIndex = int(x.group(2))
            resultMACDParam = macdParams[resultMACDParamIndex]
            fast = resultMACDParam[0]
            slow = resultMACDParam[1]
            signal = resultMACDParam[2]
        else:
            print(f"Couldn't interpret the output symbol {symbol}")
            print(output)
            continue

        x = re.search(r"Compounding Annual *[|] (\d+\.\d+)%", output)
        if x:
            annualInterest = float(x.group(1))
        else:
            print(f"Couldn't interpret the output symbol {symbol}")
            print(output)
            continue

        x = re.search(r"Sharpe Ratio *[|] (\d+\.\d+)", output)
        if x:
            sharpeRatio = float(x.group(1))
        else:
            print(f"Couldn't interpret the output symbol {symbol}")
            print(output)
            continue

        x = re.search(r"Total Trades *[|] (\d+)", output)
        if x:
            totalTrades = int(x.group(1))
        else:
            print(f"Couldn't interpret the output symbol {symbol}")
            print(output)
            continue

        print(f'self.indicators["{symbol}"] = {{"MACD": self.MACDIndicator(self, "{symbol}", {fast}, {slow}, {signal})}} #Total Trades: {totalTrades}, Compounding Annual Return: {annualInterest}, Sharpe Ratio: {sharpeRatio}', flush=True)
        elapsedOptimizeTime = timedelta(seconds=timer()-startOptimize)
        print(f"#Elapsed optimize {symbol} MACD iteration time : {elapsedOptimizeTime}")

    elapsedTotalTime = timedelta(seconds=timer() - start)
    print(f"Elapsed optimize total time : {elapsedTotalTime}")



if __name__ == "__main__":
    main()
