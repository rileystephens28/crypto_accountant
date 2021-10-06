from .base import BaseTx
from .entry_config import CASH, CRYPTO, REWARDS

# debit_crypto_base_entry = {'side': "debit", **CRYPTO}
# debit_cash_base_entry = {'side': "debit", **CASH}
# credit_base_entry = {'side': "credit",  **REWARDS}
# entry_template = {
#     'credit': credit_base_entry,
#     'debit': debit_crypto_base_entry
# }
class Reward(BaseTx):

    def __init__(self, **kwargs) -> None:
        kwargs['type'] = 'reward'
        super().__init__(**kwargs)
        # set entry templates
        self.entry_templates["base"] = [{'side': "credit",  **REWARDS}]
        if self.assets['base'].is_fiat:
            self.entry_templates["base"].append({'side': "debit", **CASH})
        else:
            self.entry_templates["base"].append({'side': "debit", **CRYPTO})
    
    def affected_balances(self):
        base = self.assets['base']
        affected_balances = {}
        affected_balances[base.symbol] = base.quantity
        if 'fee' in self.assets:
            fee = self.assets['fee']
            affected_balances[fee.symbol] = -fee.quantity
        return affected_balances
