from .base import BaseTx
from .entry_config import CRYPTO, REALIZED_GAIN_LOSS, UNREALIZED_GAIN_LOSS, CRYPTO_FAIR_VALUE_ADJ

# first, adjust to market and accrue unrealized gains.
# adj_fair_value = {'side': "debit", 'type': 'adjust', 'quantity': 0, **CRYPTO_FAIR_VALUE_ADJ}
# adj_unrealized_gains = {'side': "credit", 'type': 'adjust', 'quantity': 0, **UNREALIZED_GAIN_LOSS}
# adj_to_fair_value_entries = [adj_fair_value, adj_unrealized_gains]


# close crypto (init), adj(change), and open new cash/crypto (total) -- last out of scope of base taxable
close_crypto = {'side': "credit", **CRYPTO} # close out cost basis 
close_fair_value = {'side': "credit", **CRYPTO_FAIR_VALUE_ADJ}
close_credit_entries = [close_crypto, close_fair_value]
# open depends on type and should be implemented there via the debit transaction.

# move gains from unrealized to realized (change)
close_unrealized_gains = {'side': "debit", **UNREALIZED_GAIN_LOSS}
close_realized_gains = {'side': "credit", **REALIZED_GAIN_LOSS}
close_gain_entries = [close_unrealized_gains, close_realized_gains]


class TaxableTx(BaseTx):
    # Each taxable transaction entry should have the correct open quote, close quote, and current quote added. This will allow us to automatically derive gains, tax and (I think) equity curve

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        # check whether fee is taxable
        if 'fee' in self.assets and not self.assets['fee'].is_stable:
            self.taxable_assets = ["fee"]
        else:
            self.taxable_assets = []


    ####### INTERFACE METHODS #######

    def closing_entries(self, templates):
        # templates -> {position: [(price, qty)]}
        all_closing_entries = []
        for position, closing_vals in templates.items():
            for closing_val in closing_vals:
                all_closing_entries += self.create_closing_entry_set(position, closing_val[0], closing_val[1])
        return all_closing_entries


    ####### HELPER METHODS #######

    def create_closing_entry_set(self, asset, open_price, qty):
        # 1. adjust to market entries
        tx_asset = self.assets[asset]
        closing_val = tx_asset.usd_price * qty
        open_val = open_price * qty
        change_val = closing_val - open_val
        tx_type = self.type if asset != 'fee' else 'fee'    # may find way to make this more dynamic
        
        all_entries = []

        # 2. close crypto and fair value
        close_base_entry = {
            'mkt': asset,
            'type': tx_type,
            'quote': open_price,
            'close_quote': tx_asset.usd_price,
        }
        close_cost_basis_entry = {
            **close_crypto,
            **close_base_entry,
            'quantity': qty,  # intentionally 0, if overwritten will affect quantity which is not wanted
            'value': open_val,
        }
        close_fair_value_entry = {
            **close_fair_value,
            **close_base_entry,
            'quantity': 0,  # intentionally 0, if overwritten will affect quantity which is not wanted
            'value': -change_val,
        }
        all_entries.append(self.create_entry(**close_cost_basis_entry))
        all_entries.append(self.create_entry(**close_fair_value_entry))


        # 3. Move gains (use same value as fair value entry uses)
        close_gain_config = {
            'mkt': asset,
            'type': tx_type,
            'quantity': 0,  # intentionally 0, if overwritten will affect quantity which is not wanted
            'quote': open_price,
            'close_quote': tx_asset.usd_price,
        }
        close_unrealized_entry = {
            **close_unrealized_gains,
            **close_gain_config,
            'value': -change_val,
        }
        close_realized_entry = {
            **close_realized_gains,
            **close_gain_config,
            'value': change_val,
        }
        all_entries.append(self.create_entry(**close_unrealized_entry))
        all_entries.append(self.create_entry(**close_realized_entry))

        return all_entries
    