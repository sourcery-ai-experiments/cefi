import ccxt
from loguru import logger

from .config import settings


class CexTrader:
    """
    CEX Object to support CEFI
    exchange and trading
    via CCXT library
    https://github.com/ccxt/ccxt

    Args:
        None

    Returns:
        None

    """

    def __init__(self):
        """
        Initialize the CexTrader object

        """

        self.commands = settings.ccxt_commands
        self.cex_info = []
        logger.info(f"Loading {settings.exchanges}")
        for exchange in settings.exchanges:
            logger.info(f"Loading {exchange}")
            logger.info(f"Loading {exchange[0]}")
            client = getattr(ccxt, [exchange][0]["cex_name"])
            cx_client = client(
                {
                    "apiKey": exchange["cex_api"],
                    "secret": exchange["cex_secret"],
                    "password": (exchange["cex_password"] or ""),
                    "enableRateLimit": True,
                    "options": {
                        "defaultType": exchange["cex_defaulttype"],
                    },
                }
            )
            if exchange["cex_testmode"]:
                cx_client.set_sandbox_mode("enabled")
            account = cx_client.uid
            exchange_name = cx_client.id
            trading_asset = settings.trading_asset
            trading_risk_amount = settings.trading_risk_amount
            exchange_defaulttype = settings.cex_defaulttype
            exchange_ordertype = settings.cex_ordertype
            self.cex_info.append(
                {
                    "cex": cx_client,
                    "account": account,
                    "exchange_name": exchange_name,
                    "exchange_defaulttype": exchange_defaulttype,
                    "exchange_ordertype": exchange_ordertype,
                    "trading_asset": trading_asset,
                    "trading_risk_amount": trading_risk_amount,
                }
            )

    async def get_help(self):
        """
        Get the help information for the current instance.

        Returns:
            A string containing the available commands.
        """
        return f"{self.commands}\n"

    async def get_info(self):
        """
        Retrieves information about the exchange
        and the account.

        :return: A formatted string containing
        the exchange name and the account information.
        :rtype: str
        """

        info = ""
        for cex in self.cex_info:
            exchange_name = cex["exchange_name"]
            account = cex["account"]
            info += f"💱 {exchange_name}\n🪪 {account}\n\n"
        return info.strip()

    async def get_quotes(self, symbol):
        """
        Return a list of quotes.

        Args:
            symbol

        Returns:
            quotes
        """

        quotes = []
        for cex in self.cex_info:
            cex = cex["cex"]
            exchange_name = cex["exchange_name"]
            try:
                quote = await self.get_quote(cex, symbol)
                quotes.append(f"🏦 {exchange_name}: {quote}")
            except Exception as e:
                quotes.append(f"🏦 {exchange_name}: Error fetching quote - {e}")
        return "\n".join(quotes)

    async def get_quote(cex, symbol):
        """
        Return a quote for a symbol


        Args:
            cex
            symbol

        Returns:
            quote
        """
        ticker = cex.fetchTicker(symbol)
        return ticker.get("last") or ""

    async def get_account_balances(self):
        """
        Return account balance.

        Args:
            None

        Returns:
            balance

        """
        balance_info = []
        for cex in self.cex_info:
            cex = cex["cex"]
            exchange_name = cex["exchange_name"]
            balance = self.get_account_balance(cex)
            balance_info.append(f"🏦 Balance for {exchange_name}:\n{balance}")
        return "\n".join(balance_info)

    async def get_account_balance(cex):
        """
        return account balance.

        Args:
            None

        Returns:
            balance

        """
        raw_balance = cex.fetch_free_balance()
        filtered_balance = {
            k: v for k, v in raw_balance.items() if v is not None and v > 0
        }
        if filtered_balance:
            balance_str = "".join(
                f"{iterator}: {value} \n"
                for iterator, value in filtered_balance.items()
            )
            return f"{balance_str}"
        else:
            return "No Balance"

    async def get_account_positions(self):
        """
        return account position.

        Args:
            None

        Returns:
            position

        """

        position_info = []
        for cex in self.cex_info:
            cex = cex["cex"]
            exchange_name = cex["exchange_name"]
            positions = self.get_account_position(cex)
            position_info.append(f"📊 Position for {exchange_name}:\n{positions}")
        return "\n".join(position_info)

    async def get_account_position(cex):
        """
        return account position.

        Args:
            None

        Returns:
            position

        """
        positions = cex.fetch_positions()
        positions = [p for p in positions if p["type"] == "open"]
        if positions:
            return f"{positions}"
        return "No Position"

    async def get_account_pnl(self):
        """
        return account pnl.

        Args:
            None

        Returns:
            pnl
        """

        return 0

    async def execute_order(self, order_params):
        """
        Execute order

        Args:
            order_params (dict):
                action(str)
                instrument(str)
                quantity(int)

        Returns:
            trade_confirmation(dict)

        """
        action = order_params.get("action")
        instrument = order_params.get("instrument")
        confirmation_info = []
        if not action or not instrument:
            return

        for cex in self.cex_info:
            cex = cex["cex"]
            exchange_name = cex["exchange_name"]
            order_type = cex["exchange_ordertype"]
            try:
                if await self.get_balance(cex) == "No Balance":
                    logger.debug("⚠️ Check Balance")
                    continue
                asset_out_quote = float(cex.fetchTicker(f"{instrument}").get("last"))
                asset_out_balance = float(
                    cex.fetchBalance()[f"{cex['trading_asset']}"]["free"]
                )

                if not asset_out_balance:
                    continue

                quantity = order_params.get("quantity", cex["trading_risk_amount"])
                transaction_amount = (
                    asset_out_balance * (float(quantity) / 100) / asset_out_quote
                )

                trade = cex.create_order(
                    instrument,
                    order_type,
                    action,
                    transaction_amount,
                    # price=None
                )

                if not trade:
                    continue

                trade_confirmation = (
                    f"⬇️ {instrument}" if (action == "SELL") else f"⬆️ {instrument}\n"
                )
                trade_confirmation += f"➕ Size: {round(trade['amount'], 4)}\n"
                trade_confirmation += f"⚫️ Entry: {round(trade['price'], 4)}\n"
                trade_confirmation += f"ℹ️ {trade['id']}\n"
                trade_confirmation += f"🗓️ {trade['datetime']}"
                if trade_confirmation:
                    confirmation_info.append(f"{exchange_name}:\n{trade_confirmation}")
                else:
                    confirmation_info.append(f"Error executing {exchange_name}")

            except Exception as e:
                confirmation_info.append(f"{exchange_name}: {e}")
                continue

        return confirmation_info
