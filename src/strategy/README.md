# QuantConnect trading strategies
This folder contains trading strategies developed using [QuantConnect Lean dev environemnt](https://www.lean.io/) also see [Lean on Github](https://github.com/QuantConnect/Lean)

## Preparation of local dev environment
There are [at least 2 ways](https://github.com/QuantConnect/Lean/blob/master/.vscode/readme.md) to set up local env for Lean development. Arguably, the easiest way to do it, is to set up [Lean CLI](https://github.com/QuantConnect/lean-cli) - this is command line tool that facilitates number of Lean trading strategy development tasks. For better productivity I suggest using [Git Bash](https://gitforwindows.org/) if you are Windows user.

This is [the original set up instructions](https://www.quantconnect.com/docs/v2/lean-cli/getting-started/lean-cli). You can also follow the steps that I tried locally at my machine:
1. Ensure you have latest Python3 environment (preferably using Anaconda or direct installation). If you were able to run `pip install --upgrade -r requirements.txt` from the [root README](https://github.com/iskaspb/project-omega#readme) than you are good. If you are not sure you can run this command:
```
$ pip install --upgrade lean
```
2. [Install Docker](https://www.lean.io/docs/lean-cli/tutorials/installation/installing-docker) and run it **before the next step**;
3. Assuming you "`git clone ...`" this repo into something like `~/fintech/project-omega`, please execute in the folder `~/fintech/project-omega/src/strategy` (it will take some time):
```
$ lean init
```
4. So now you are ready to run a local backtest; please run this:
```
$ lean backtest HodlSPY
```
You will see an output similar to this:
```
...
STATISTICS:: Total Trades 1
STATISTICS:: Average Win 0%
STATISTICS:: Average Loss 0%
STATISTICS:: Compounding Annual Return 271.453%
STATISTICS:: Drawdown 2.200%
STATISTICS:: Expectancy 0
STATISTICS:: Net Profit 1.692%
STATISTICS:: Sharpe Ratio 8.888
STATISTICS:: Probabilistic Sharpe Ratio 67.609%
STATISTICS:: Loss Rate 0%
STATISTICS:: Win Rate 0%
STATISTICS:: Profit-Loss Ratio 0
STATISTICS:: Alpha -0.005
STATISTICS:: Beta 0.996
STATISTICS:: Annual Standard Deviation 0.222
STATISTICS:: Annual Variance 0.049
STATISTICS:: Information Ratio -14.565
STATISTICS:: Tracking Error 0.001
STATISTICS:: Treynor Ratio 1.978
STATISTICS:: Total Fees $3.44
...
```
5. If you want to create a new trading strategy you can run this command:
```
 $ lean create-project your-strategy-name
```