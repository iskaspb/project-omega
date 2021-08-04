from pandas._libs.tslibs.timestamps import Timestamp
import yfinance as yf
import pandas as pd
import argparse
import datetime
import logging
import pprint
import json
import sys
import os



def initArgparse() -> argparse.ArgumentParser:
    def make_wide(formatter, w=120, h=36):
        """Return a wider HelpFormatter, if possible."""
        try:
            # https://stackoverflow.com/a/5464440
            kwargs = {'width': w, 'max_help_position': h}
            formatter(None, **kwargs)
            return lambda prog: formatter(prog, **kwargs)
        except TypeError:
            return formatter

    parser = argparse.ArgumentParser(
        usage="%(prog)s [OPTIONS]...",
        description="Fetches historical data for strategies' backtests",
        formatter_class=make_wide(argparse.HelpFormatter, w=80, h=20)
    )

    parser.add_argument(
        "-v", "--version", action="version",
        version=f"{parser.prog} version 1.0.0"
    )

    loglevels = ["DEBUG", "INFO", "WARN", "ERROR", "FATAL"]
    parser.add_argument(
        "-l", "--loglevel", metavar="LOGLEVEL",
        default="INFO", choices=loglevels,
        help=f"Set LOGLEVEL{loglevels} [default='INFO']"
    )

    def getDefultConfigFilename():
        return os.path.splitext(sys.argv[0])[0] + ".json"

    defaultConfig = getDefultConfigFilename()
    parser.add_argument(
        "-c", "--config", default=defaultConfig,
        help=f"Set configuration [default={defaultConfig}]"
    )

    parser.add_argument(
        "-f", "--force", action='store_true', default=False,
        help="Overwrite existing data files [default=(do not overwrite)]"
    )

    parser.add_argument(
        "-d", "--dryrun", action='store_true', default=False,
        help="Read config and validate target folders but don't download any data"
    )

    return parser

class ConfigError(Exception):
    pass

def parseConfig(configJson):

    def collectSymbolsConfig(configJson) -> dict:

        def collectSymbolConfigParams(configSectionName, paramsJson) -> dict:
            params = {}
            currentDate = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            if "period" in paramsJson:
                periodJson = paramsJson["period"]

                if "start" in periodJson:
                    start = datetime.datetime.strptime(periodJson["start"], "%Y-%m-%d")
                else:
                    raise ConfigError(f"[{configSectionName}] Config doesn't have mandatory 'period.start' field")
                if start >= currentDate:
                    raise ConfigError(f"[{configSectionName}] Config start[{start}] must be before current date[{currentDate}]")

                if "end" in periodJson:
                    end = datetime.datetime.strptime(periodJson["end"], "%Y-%m-%d")
                    if start < end:
                        params["period"] = {"start" : start, "end" : end}
                    elif start == end:
                        raise ConfigError(f"[{configSectionName}] Config period start[{start}] == end[{end}]")
                    else:
                        logging.warn(f"[{configSectionName}] Config period start[{start}] > end[{end}]. Fixing it by swapping 2 values")
                        params["period"] = {"start" : end, "end" : start}
                else:
                    params["period"] = {"start" : start, "end" : currentDate}

            params["symbols"] = paramsJson.get("symbols", [])

            if len(params["symbols"]) and not "period" in params:
                raise ConfigError(f"[{configSectionName}] Config has symbols but doesn't have period. Please specify period (or remove symbols)")
            if not len(params["symbols"]) and "period" in params:
                raise ConfigError(f"[{configSectionName}] Config doesn't have symbols but has period. Please specify symbols (or remove period)")

            return params

        def mergeSymbolsConfig(symbolsConfig, params) -> dict:
            newPeriod = params["period"]
            for symbol in params["symbols"]:
                if symbol in symbolsConfig:
                    existingPeriod = symbolsConfig[symbol]["period"]
                    symbolsConfig[symbol] = {
                        "period": {
                            "start" : min(existingPeriod["start"], newPeriod["start"]),
                            "end"   : max(existingPeriod["end"], newPeriod["end"])
                        }
                    }
                else:
                    symbolsConfig[symbol] = {"period" : newPeriod}

        symbolsConfig = {}
        configSectionName = "TopLevel"
        globalParams = collectSymbolConfigParams(configSectionName, configJson)
        mergeSymbolsConfig(symbolsConfig, globalParams)
        if "strategy" in configJson:
            for stratJson in configJson["strategy"]:
                configSectionName = stratJson.get("name", "UnknownStrat")
                stratParams = collectSymbolConfigParams(configSectionName, stratJson)
                if len(stratParams["symbols"]):
                    mergeSymbolsConfig(symbolsConfig, stratParams)
                else:
                    logging.warn(f"[{configSectionName}] Config doesn't have symbols. This section will be skipped")

        if not len(symbolsConfig):
            logging.warn("Config doesn't have symbols. Nothing to download")

        return symbolsConfig

    def collectInterval(configJson) -> str:
        if "interval" in configJson:
            return configJson["interval"]
        else:
            raise ConfigError("[TopLevel] Config must contain 'interval' field, possible values : [1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo]")

    def collectFolder(configJson) -> str:
        if "folder" in configJson:
            return configJson["folder"]
        else:
            raise ConfigError("[TopLevel] Config must contain 'folder' field")

    symbolsFetchConfig = {
        "symbols" : collectSymbolsConfig(configJson),
        "interval" : collectInterval(configJson),
        "folder" : collectFolder(configJson)
        }

    return symbolsFetchConfig


def fetchData(args) -> None:
    logging.info(f"Loading configuration from file : {args.config}")
    with open(args.config) as configFile:
        baseDir = os.path.dirname(os.path.abspath(args.config))
        logging.debug(f"Config folder : {baseDir}")

        config = json.load(configFile)
        symbolsFetchConfig = parseConfig(config)
        logging.debug(f"Use parsed config to fetch symbol data:\n{pprint.pformat(symbolsFetchConfig)}")

        def prepareFolder(baseDir, folder):
            if not os.path.isabs(folder):
                folder = os.path.normpath(os.path.join(baseDir, folder))
            if os.path.exists(folder):
                if not os.path.isdir(folder):
                    raise Exception(f"Path {folder} exists but it's not a folder. Please review your data folder strurcture")
            else:
                logging.info(f"Folder {folder} doesn't exist. Creating it...")
                os.mkdir(folder)
            return folder
        
        symbolFolder = prepareFolder(baseDir, symbolsFetchConfig["folder"])

        for symbol, symbolConfig in symbolsFetchConfig["symbols"].items():
            symbolFilename = symbol.lower() + ".zip"
            symbolPath = os.path.join(symbolFolder, symbolFilename)
            symbolStart = symbolConfig["period"]["start"]
            symbolEnd = symbolConfig["period"]["end"]

            shouldReplaceExistingFile = False
            if os.path.exists(symbolPath):
                if not os.path.isfile(symbolPath):
                    raise Exception(f"Target symbol {symbol} path is not a regular file: {symbolPath}. Please review your data folder structure")
                df = pd.read_csv(symbolPath, names=["Date","Open","High","Low","Close","Volume"])
                logging.debug(f"First line :\n{df.head(1)}")
                logging.debug(f"File dates : [{df.iloc[0]['Date']},{df.iloc[-1]['Date']}]")
                fileStart = datetime.datetime.strptime(df.iloc[0]['Date'], "%Y%m%d %H:%M")
                fileEnd = datetime.datetime.strptime(df.iloc[-1]['Date'], "%Y%m%d %H:%M")

                if symbolStart < fileStart or fileEnd < symbolEnd:
                    logMsg = (
                        f"Symbol {symbol} file exists : {symbolPath}. "
                        f"However it doesn't contain required historical period. "
                        f"File dates [{fileStart},{fileEnd}]. "
                        f"Configured dates [{symbolStart},{symbolEnd}].")
                else:
                    logMsg = (
                        f"Symbol {symbol} file exists : {symbolPath}. "
                        f"It contains larger period of histrocal data. "
                        f"File dates [{fileStart},{fileEnd}]. "
                        f"Configured dates [{symbolStart},{symbolEnd}].")

                if args.force:
                    logging.info(logMsg + " Force override the data file (--force is selected).")
                    shouldReplaceExistingFile = True
                else:
                    logging.warning(logMsg + " Skipping symbol download (you can use --force to enforce it).")
                    continue

            logging.info(f"Downloading {symbol} : {symbolConfig}")
            df = yf.download(
                symbol,
                start=symbolStart,
                end=symbolEnd,
                interval=symbolsFetchConfig["interval"],
                auto_adjust = True
                )
            def yahooFinanceDateToQuantConnect(yfDate : Timestamp) -> str:
                # 2021-06-30 -> 20210630 00:00
                #return yfDate.translate({ord('-'): None}) + " 00:00"
                return yfDate.strftime("%Y%m%d %H:%M")
            def yahooFinanceNumToQuantConnect(yfNum : float) -> int:
                # 427.209991 -> 4272099
                return int(yfNum * 10000)
            logging.debug(f"got data\n{df.head(1)}")
            df.reset_index(level=0, inplace=True)

            df["QCDate"]  = df["Date"].transform(yahooFinanceDateToQuantConnect)
            df["QCOpen"]  = df["Open"].transform(yahooFinanceNumToQuantConnect)
            df["QCHigh"]  = df["High"].transform(yahooFinanceNumToQuantConnect)
            df["QCLow"]   = df["Low"].transform(yahooFinanceNumToQuantConnect)
            df["QCClose"] = df["Close"].transform(yahooFinanceNumToQuantConnect)

            logging.debug(f"convert data format\n{df[['QCDate', 'QCOpen', 'QCHigh', 'QCLow', 'QCClose', 'Volume']].head(1)}")

            downloadSymbolPath = symbolPath + ".download"
            csvFileName = symbol.lower() + ".csv"
            df[['QCDate', 'QCOpen', 'QCHigh', 'QCLow', 'QCClose', 'Volume']].to_csv(
                downloadSymbolPath,
                index=False,
                header=False,
                compression={
                    "method" : 'zip',
                    "archive_name" : csvFileName
                    }
                )
            if shouldReplaceExistingFile:
                os.replace(downloadSymbolPath, symbolPath)
            else:
                os.rename(downloadSymbolPath, symbolPath)



def main() -> None:
    parser = initArgparse()
    args = parser.parse_args()

    logging.basicConfig(format="%(asctime)s %(levelname)-4s %(message)s", level=logging.getLevelName(args.loglevel), datefmt="%Y-%m-%d %H:%M:%S")

    fetchData(args)

if __name__ == "__main__":
    main()



