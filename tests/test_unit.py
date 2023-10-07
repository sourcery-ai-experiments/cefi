from datetime import datetime

import pytest

from cefi import CexTrader
from cefi.config import settings


@pytest.fixture(scope="session", autouse=True)
def set_test_settings_CEX():
    settings.configure(FORCE_ENV_FOR_DYNACONF="cefi")


@pytest.fixture(name="order")
def order1():
    """return standard expected results"""
    return {
        "action": "BUY",
        "instrument": "BTC",
        "stop_loss": 2000,
        "take_profit": 400,
        "quantity": 10,
        "order_type": None,
        "leverage_type": None,
        "comment": None,
        "timestamp": datetime.now(),
    }


@pytest.fixture(name="limit_order")
def order2():
    """return standard expected results"""
    return {
        "action": "BUY",
        "instrument": "BNB",
        "stop_loss": 2000,
        "take_profit": 400,
        "quantity": 10,
        "comment": None,
        "timestamp": datetime.now(),
    }


@pytest.fixture(name="CXTrader")
def test_fixture():
    return CexTrader()


def test_dynaconf_is_in_testing_env_CEX():
    print(settings.VALUE)
    assert settings.VALUE == "On Testing CEX"

# @pytest.mark.asyncio
# async def test_cefi_exception():
#     with pytest.raises(Exception):
#         return CexTrader("123")
        

@pytest.mark.asyncio
async def test_cefi(CXTrader):
    print(type(CXTrader))
    result = await CXTrader.get_info()
    assert "ℹ️" in result
    assert "💱 binance" in result
    assert CXTrader is not None
    assert isinstance(CXTrader, CexTrader)
    assert callable(CXTrader.get_balances)
    assert callable(CXTrader.get_positions)
    assert callable(CXTrader.submit_order)


@pytest.mark.asyncio
async def test_quote(CXTrader, caplog):
    """Test quote"""
    result = await CXTrader.get_quotes("BTC")
    assert result is not None
    assert "⚖️" in result
    assert ("binance" in result) or ("huobi" in result)
    assert ("No Quote" in result) or ("2" in result)


@pytest.mark.asyncio
async def test_get_balances(CXTrader):
    """Test balance"""
    result = await CXTrader.get_balances()
    assert result is not None
    assert "💵" in result
    assert ("binance" in result) or ("huobi" in result)


@pytest.mark.asyncio
async def test_get_positions(CXTrader):
    result = await CXTrader.get_positions()
    assert "📊" in result


@pytest.mark.asyncio
async def test_get_pnls(CXTrader):
    """Test pnl"""
    result = await CXTrader.get_pnls()
    assert "📊" in result


@pytest.mark.asyncio
async def test_submit_order(CXTrader, order):
    result = await CXTrader.submit_order(order)
    assert result is not None
    print(result)
    assert "binance" in result[0]
    assert "🔵" in result[0] or ("Error" in result[0])
    assert "huobi" in result[1]
    assert ("🔵" in result[1]) or ("Error" in result[1])

@pytest.mark.asyncio
async def test_submit_order_exception(CXTrader):
    with pytest.raises(Exception):
        CXTrader.clients=[]
        await CXTrader.submit_order()
        
# @pytest.mark.asyncio
# async def test_submit_limit_order(CXTrader, limit_order):
#     result = await CXTrader.submit_order(limit_order)
#     assert result is not None
#     print(result)
#     assert "binance" in result
#     assert "🔵" in result or ("Error" in result)



@pytest.mark.asyncio
async def test_get_trade_confirmation(CXTrader):
    # Create a mock trade object and test different cases
    trade_buy = {
        'amount': 10.0,
        'price': 100.0,
        'takeProfitPrice': 110.0,
        'stopLossPrice': 90.0,
        'id': '12345',
        'datetime': '2023-10-07 12:00:00'
    }

    trade_sell = {
        'amount': 10.0,
        'price': 100.0,
        'takeProfitPrice': 110.0,
        'stopLossPrice': 90.0,
        'id': '67890',
        'datetime': '2023-10-07 14:00:00'
    }

    for client in CXTrader.clients:
        result = await client.get_trade_confirmation(
        trade_sell,
        "InstrumentName",
        "SELL")
        assert ("binance" in result) or ("huobi" in result)
        assert "⬇️" in result
        assert "⚫" in result
        assert "🔵" in result
        assert "🟢" in result
        assert "🗓️" in result
