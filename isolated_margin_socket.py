import asyncio
import json
import os
import logging
import requests
from binance import AsyncClient, BinanceSocketManager

api_key = os.environ.get("BINANCE_API_KEY")
api_secret = os.environ.get("BINANCE_SECRET_KEY")
token = os.environ.get("TELEGRAM_TOKEN")
chat_id = os.environ.get("TELEGRAM_CHAT_ID")
symbol = os.environ.get("ISOLATED_MARGIN_SYMBOL")

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt="%m/%d/%Y %I:%M:%S %p %Z", level=logging.INFO)
logger = logging.getLogger(__name__)



def send_telegram(text):
    try:
        dt = {'chat_id': chat_id, 'text': text, 'parse_mode': "html"}
        res = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage", params=dt)
        ok = res.json()
        if not ok['ok']:
            logging.error(f"Error From telegram: {ok}\n")
        else:
            logging.debug(f"From telegram: {ok}\n")
    except Exception as E:
        logging.error(
            f"Exception on processing send_telegram https requests: {str(E)}\n")


def process_message(msg):
    try:
        logging.info(f"Isolated Margin Socket Message Received: {msg['e']}")
        if msg['e'] == "executionReport":
            order_id = msg['i']
            price = msg['p']
            symbol = msg['s']
            side = msg['S']
            order_quantity = msg['q']
            current_execution_type = msg['x']
            current_order_status = msg['X']
            last_executed_quantity = msg['l']
            cumulative_filled_quantity = msg['z']
            try:
                if current_execution_type == 'NEW':
                    txt = f"✅ ✅ ✅\n<b>Isolated Margin Order CREATED\nSide:</b> {side}\n<b>Symbol:</b> #{symbol}\n<b>Price:</b> {price}\n<b>Quantity:</b> {order_quantity}\n<b>Order ID:</b> #ID{order_id}"
                elif current_execution_type == 'CANCELED':
                    txt = f"🛑 🛑 🛑\n<b>Isolated Margin Order CANCELED\nSide:</b> {side}\n<b>Symbol:</b> #{symbol}\n<b>Price:</b> {price}\n<b>Quantity:</b> {order_quantity}\n<b>Order ID:</b> #ID{order_id}"
                elif current_execution_type == 'TRADE':
                    if current_order_status == 'PARTIALLY_FILLED':
                        txt = f"💰\n<b>Isolated Margin Order PARTIALLY FILLED\nSide:</b> {side}\n<b>Symbol:</b> #{symbol}\n<b>Price:</b> {price}\n<b>Last Filled:</b> {last_executed_quantity}\n<b>Remaining:</b> {float(order_quantity) - float(cumulative_filled_quantity)}\n<b>Order ID:</b> #ID{order_id}"
                    elif current_order_status == 'FILLED':
                        txt = f"💰 💰 💰\n<b>Isolated Margin Order FULLY FILLED\nSide:</b> {side}\n<b>Symbol:</b> #{symbol}\n<b>Price:</b> {price}\n<b>Filled:</b> {cumulative_filled_quantity}\n<b>Order ID:</b> #ID{order_id}"
                    else:
                        txt = f"❌ ❌ ❌\n<b>In Isolated Margin: Else Condition, current_execution_type == TRADE >></b>\n{msg}"
                elif current_execution_type in ['REPLACED', 'REJECTED', 'EXPIRED', 'PENDING_CANCEL']:
                    txt = f"🚫 🚫 🚫\n<b>Isolated Margin Order {current_execution_type}\nSide:</b> {side}\n<b>Symbol:</b> #{symbol}\n<b>Price:</b> {price}\n<b>Quantity:</b> {order_quantity}\n<b>Order ID:</b> #ID{order_id}"
                else:
                    txt = f'⚠️ ⚠️ ⚠️\n<b> ,Undefined Current Execution Type Condition In Isolated Margin market >></b>\n{msg}'
                send_telegram(txt)
                logging.debug(
                    f"Isolated Margin Message Processed for telegram:{txt}")
            except Exception as E:
                ee = str(
                    f"In Isolated Margin, Exception found on executionReport\n{str(E)}")
                logging.error(ee)
                send_telegram(ee)
    except Exception as E:
        ee = str(
            f"In Isolated Margin, Exception found on processed message: {str(E)}")
        logging.error(ee)
        send_telegram(ee)


async def isolated_margin_user(client, isolated_margin_symbol):
    """
    :param client: Binance API client
    :type client: binance.AsyncClient

    :param isolated_margin_symbol[optional]: binance isolated margin symbol default "BNBBTC"
    :type isolated_margin_symbol: str
    """
    bm = BinanceSocketManager(client)  # , user_timeout=1700
    logger.info(
        f"Binance Starts a web socket Manager for isolated margin symbol={isolated_margin_symbol}..")
    async with bm.isolated_margin_socket(isolated_margin_symbol) as stream:
        while True:
            res = await stream.recv()
            if res is not None and "e" in res:
                process_message(res)
                print(json.dumps(res, indent=2))
            else:
                continue


async def main():
    client = await AsyncClient.create(api_key=api_key, api_secret=api_secret)
    await isolated_margin_user(client=client,isolated_margin_symbol= symbol)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
