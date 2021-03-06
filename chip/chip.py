from iconservice import *

TAG = 'BLACKJACK_TOKEN'


class TokenFallbackInterface(InterfaceScore):
    @interface
    def tokenFallback(self, _from: Address, _value: int, _data: bytes):
        pass


class Chip(IconScoreBase):
    _BALANCES = 'balances'
    _TOTAL_SUPPLY = 'total_supply'
    _DECIMALS = 'decimals'

    @eventlog(indexed=3)
    def Transfer(self, _from: Address, _to: Address, _value: int, _data: bytes):
        pass

    @eventlog(indexed=2)
    def Burn(self, _from: Address, _value: int):
        pass

    def on_install(self, decimals: int = 0) -> None:
        super().on_install()

        self._total_supply.set(0)
        self._decimals.set(decimals)

    def on_update(self) -> None:
        super().on_update()
        pass

    def __init__(self, db: 'IconScoreDatabase') -> None:
        super().__init__(db)
        self._balances = DictDB(self._BALANCES, db, value_type=int)
        self._decimals = VarDB(self._DECIMALS, db, value_type=int)
        self._total_supply = VarDB(self._TOTAL_SUPPLY, db, value_type=int)

    @external(readonly=True)
    def name(self) -> str:
        """
        :return: The name of Token.
        """
        return "blackjack chips"

    @external(readonly=True)
    def symbol(self) -> str:
        """
        :return: The symbol of Token.
        """
        return "chips"

    @external(readonly=True)
    def decimals(self) -> int:
        """
        :return: The value of decimals. [Chip * 10 ** decimals = ICX]
        """
        return self._decimals.get()

    @external(readonly=True)
    def totalSupply(self) -> int:
        """
        :return: The overall amount of minted chips for game
        """
        return self._total_supply.get()

    @external(readonly=True)
    def balanceOf(self, _owner: Address) -> int:
        """
        :param _owner: The owner of Chips
        :return: The amount of chips owned by _owner
        """
        return self._balances[_owner]

    @external
    def mint(self, amount: int):
        """
        This method should be invoked by CA not EOA.

        :param amount: the amount of Chips to mint
        """
        if not self.msg.sender.is_contract:
            revert("This method should be invoked by CA not EOA")

        self._balances[self.tx.origin] = self._balances[self.tx.origin] + amount * (10 ** self._decimals.get())

    @external
    def burn(self, amount: int):
        """
        This method should be invoked by CA not EOA.

        :param amount: the icx amount for Chips to exchange
        """
        if not self.msg.sender.is_contract:
            revert("This method should be invoked by CA not EOA")

        if self._balances[self.tx.origin] > amount:
            self._burn(self.tx.origin, amount * (10 ** self._decimals.get()))
            self.Burn(self.tx.origin, amount * (10 ** self._decimals.get()))
        else:
            revert(f"You don't have enough chips to burn. Your balance: {self._balances[self.tx.origin]}")

    @external
    def transfer(self, _to: Address, _value: int, _data: bytes = None):
        if _value < 0:
            revert('Transferring value cannot be less than zero')
        if self._balances[self.tx.origin] < _value:
            revert("Out of balance")

        self._balances[self.tx.origin] = self._balances[self.tx.origin] - _value
        self._balances[_to] = self._balances[_to] + _value

        # Emits an event log `Transfer`
        self.Transfer(self.tx.origin, _to, _value, _data)
        Logger.debug(f'Transfer({self.tx.origin},{_to},{_value},{_data})', TAG)

    def _burn(self, address: Address, amount: int):
        self._balances[address] = self._balances[address] - amount
