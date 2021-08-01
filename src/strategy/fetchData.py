import argparse
import datetime
import logging
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

    defaultConfig = os.path.splitext(sys.argv[0])[0] + ".json"
    parser.add_argument(
        "-c", "--config", default=defaultConfig,
        help=f"Set configuration [default={defaultConfig}]"
    )

    parser.add_argument(
        "-f", "--force", action='store_true', default=False,
        help="Overwrite existing data files [default=(do not overwrite)]"
    )

    return parser

class ConfigError(Exception):
    pass

def parseConfig(configJson):

    def getParams(name, paramsJson):
        params = {}
        currentDate = datetime.datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if "period" in paramsJson:
            periodJson = paramsJson["period"]

            if "start" in periodJson:
                start = datetime.datetime.strptime(periodJson["start"], "%Y-%m-%d")
            else:
                raise ConfigError(f"[{name}] Config doesn't have mandatory 'period.start' field")
            if start >= currentDate:
                raise ConfigError(f"[{name}] Config start[{start}] must be before current date[{currentDate}]")

            if "end" in periodJson:
                end = datetime.datetime.strptime(periodJson["end"], "%Y-%m-%d")
                if start < end:
                    params["start"] = start
                    params["end"] = end
                elif start == end:
                    raise ConfigError(f"[{name}] Config period start[{start}] == end[{end}]")
                else:
                    logging.warn(f"[{name}] Config period start[{start}] > end[{end}]. Fixing it by swapping 2 values")
                    params["start"] = end
                    params["end"] = start
            else:
                params["start"] = start
                params["end"] = currentDate

        else:
            raise ConfigError(f"[{name}] Config doesn't have mandatory 'period' field")
        params["symbols"] = paramsJson.get("symbols", [])
        return params

    def populateSymbols(symbols, params):
        start = params["start"]
        end = params["end"]
        for symbol in params["symbols"]:
            if symbol in symbols:
                (symStart, symEnd) = symbols[symbol]

                if not symStart:
                    symStart = start
                elif start:
                    symStart = min(start, symStart)

                if not symEnd:
                    symEnd = end
                elif end:
                    symEnd = max(end, symEnd)

                symbols[symbol] = (symStart, symEnd)
            else:
                symbols[symbol] = (start, end)

    downloadConfig = {"symbols" : {}}
    if "interval" in configJson:
        downloadConfig["interval"] = configJson["interval"]
    else:
        raise ConfigError("[TopLevel] Config must contain 'interval' field, possible values : [1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo]")
    
    if "folder" in configJson:
        downloadConfig["folder"] = configJson["folder"]
    else:
        raise ConfigError("[TopLevel] Config must contain 'folder' field")

    globalParams = getParams("TopLevel", configJson)
    populateSymbols(downloadConfig["symbols"], globalParams)

    if "strategy" in configJson:
        for stratJson in configJson["strategy"]:
            name = stratJson.get("name", "UnknownStrat")
            stratParams = getParams(name, stratJson)
            populateSymbols(downloadConfig["symbols"], stratParams)

    return downloadConfig


def fetchData(args) -> None:
    logging.info(f"Loading configuration from file : {args.config}")
    with open(args.config) as configFile:
        baseDir = os.path.dirname(os.path.abspath(args.config))
        logging.debug(f"Config folder : {baseDir}")

        config = json.load(configFile)
        downloadConfig = parseConfig(config)
        logging.debug(f"Download config : {downloadConfig}")

def main() -> None:
    parser = initArgparse()
    args = parser.parse_args()

    logging.basicConfig(format="%(asctime)s %(levelname)-4s %(message)s", level=logging.getLevelName(args.loglevel), datefmt="%Y-%m-%d %H:%M:%S")

    fetchData(args)

if __name__ == "__main__":
    main()



