import subprocess
import re

def GenerateMACDParams() -> list:
    # instead of standard macd(12,26) with a 9 day signal we try different values
    macdParams = [(12, 26, 9)]
    slowRange = range(10, 30)
    fastRange = range(5, 15)
    signalRange = range(2, 10)
    for slow in slowRange:
        for fast in fastRange:
            for signal in signalRange:
                if signal < fast and fast < slow:
                    validParam = (fast, slow, signal)
                    if macdParams[0] != validParam:
                        macdParams.append(validParam)
    return macdParams


def main() -> None:
    macdParams = GenerateMACDParams()
    print(f"MACD parameters generated : {len(macdParams)}")
    #macdParamIndex = 1043
    #print(f"macdParams[{macdParamIndex}]={macdParams[macdParamIndex]}")
    symbols = sorted(set(["AAPL", "BABA", "TSLA", "INTC", "NVDA", "MU", "FB", "WMT", "AMD", "AMZN", "GOOG", "HP", "GE", "F", "T",  "BAC", "CSCO", "KO", "PINS", "PG", "PEP", "UPS", "PYPL"]))
    print(f"Optimize for {len(symbols)} symbols : {symbols}")

    for symbolIndex in range(0, len(symbols)-1):
        symbol = symbols[symbolIndex]
        optimizeCmd = ["lean", "optimize", "--strategy", 'Grid Search', "--target", 'Sharpe Ratio', "--target-direction", "max", "--parameter", "macd-param-index", "0", f"{len(macdParams)-1}", "1", "--parameter", "symbol-index", f"{symbolIndex}", f"{symbolIndex}", "1", "MACD_Simple"]
        print(f"#optimize for symbol {symbol} : {' '.join(optimizeCmd)}", flush=True)
        process = subprocess.Popen(optimizeCmd, stdout=subprocess.PIPE)
        output, error = process.communicate()
        output = output.decode('utf-8', 'ignore')[-3000:]
        x = re.search(r"Optimal parameters: symbol-index: (\d+), macd-param-index: (\d+)", output)
        if not x:
            print(f"Couldn't interpret the output symbol {symbol}: {output}")
            continue
        resultSymbolIndex = int(x.group(1))
        if symbolIndex != resultSymbolIndex:
            print(f"Wrong symbol index! Expecting {symbolIndex} however got {resultSymbolIndex}")
        resultMACDParamIndex = int(x.group(2))
        resultMACDParam = macdParams[resultMACDParamIndex]
        fast = resultMACDParam[0]
        slow = resultMACDParam[1]
        signal = resultMACDParam[2]
        x = re.search(r"Compounding Annual.*| (\d+\.\d+)%", output)
        if not x:
            print(f"Couldn't interpret the output symbol {symbol}: {output}")
            continue
        annualInterest = float(x.group(1))
        if annualInterest < 15.0:
            print(f'self.indicators[{symbol}] = {{"MACD": self.MACDIndicator(self, {symbol}, {fast}, {slow}, {signal})}} #Interest is too low: {annualInterest}', flush=True)
        else:
            print(f'self.indicators[{symbol}] = {{"MACD": self.MACDIndicator(self, {symbol}, {fast}, {slow}, {signal})}} #Interest: {annualInterest}', flush=True)


if __name__ == "__main__":
    main()
