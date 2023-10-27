import json
import httpx


async def get_price(token: str) -> float:
    """
    Получение **стоимости** токена в **USD** через API сервиса CryptoCompare.

    :param token: идентификатор токена (ETH, USDC, USDT...)
    :return: :class:`float` – стоимость с 2 знаками после запятой.
    """
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"https://min-api.cryptocompare.com/data/price?fsym={token}&tsyms=USD")
        resp_json = resp.json()

        if "USD" not in resp_json:
            return 0.0

        return float(resp_json["USD"])


class AsyncFetcher:

    API_URL = "https://block-explorer-api.mainnet.zksync.io"

    def __init__(self, address: str):
        self.address = address

        with open("contracts.json", "r") as file:
            self.contracts = json.load(file)["contracts"]

    async def fetch_and_sort(self) -> dict:
        results = {}
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                url=f"{AsyncFetcher.API_URL}/transactions",
                params={
                    "address": self.address,
                    "limit": 100
                }
            )

            response = resp.json()["items"]

        for tx in response:
            for name, data in self.contracts.items():
                if "interactions" not in results:
                    results["interactions"] = 0

                if name not in results:
                    results[name] = 0

                if str(tx["to"]).lower() == str(data["contract"]).lower() and tx["status"] != "failed":
                    results[name] += 1
                    results["interactions"] += 1

            if "Era Bridge" not in results:
                results["Era Bridge"] = 0

            if tx["isL1Originated"]:
                results["Era Bridge"] += 1
                results["interactions"] += 1

            if "total" not in results:
                results["total"] = len(response)

            if "total_fee" not in results:
                results["total_fee"] = 0

            if str(tx["from"]).lower() == self.address.lower():
                results["total_fee"] += round(float(int(tx["fee"], base=16) / 10 ** 18), 6)

        return results

    async def get_balances(self) -> dict:
        """
        Получение всех доступных балансов всех токенов по адресу.

        Если токен есть в списке известных (типа **ETH**, **USDC**, **USDT**),
        то будет сохранена его стоимость в **USD**.

        :return: :class:`dict` – словарь с данными
        """
        results = {}
        async with httpx.AsyncClient() as client:
            response = await client.get(url=f"{AsyncFetcher.API_URL}/address/{self.address}")
            response_json = response.json()["balances"]

        for address, data in response_json.items():
            if data["token"] is None:
                continue

            symbol = data["token"]["symbol"]

            decimals = data["token"]["decimals"]
            balance = round(int(data["balance"]) / 10 ** decimals, 6)

            if balance == 0:
                continue

            price = await get_price(symbol)

            results[symbol] = {
                "balance": balance,
                "usd_value": round(balance * price, 2) if symbol in ["ETH", "USDT", "USDC"] else "* * *"
            }

        return results


async def fetch_data(address):
    fetcher = AsyncFetcher(address)
    transactions = await fetcher.fetch_and_sort()
    balances = await fetcher.get_balances()
    return {
        "tx": transactions,
        "balances": balances
    }
