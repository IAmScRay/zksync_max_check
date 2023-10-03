import time
from threading import Thread

from fetcher import Fetcher


class StatsThread(Thread):
    """
    Поток для параллельного получения данных о транзакциях.
    """

    def __init__(
            self,
            accounts: list,
            name: str
    ):
        """
        Инициализация объекта.

        :param accounts: список адресов, статистику которых нужно получить
        :param name: имя для потока
        """
        super().__init__(name=name)

        self.accounts = accounts
        self.results = {}

    def run(self):
        """
        Запуск потока.

        Через объект :class:`Fetcher` получаются все данные, а результат
        хранится в ``self.results``.
        """
        print(f"Запушен поток {self.getName()}")
        time.sleep(1)

        r = range(0, len(self.accounts))
        for index in r:
            address = self.accounts[index]
            fetcher = Fetcher(address)

            transactions = fetcher.fetch_and_sort()
            balances = fetcher.get_balances()

            self.results[address] = {
                "tx": transactions,
                "balances": balances
            }
