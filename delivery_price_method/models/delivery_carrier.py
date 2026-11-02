# Copyright 2020 Trey, Kilobytes de Soluciones
# Copyright 2020 Tecnativa - Pedro M. Baeza
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class DeliveryCarrier(models.Model):
    _inherit = "delivery.carrier"

    # pylint: disable=W8113
    price_method = fields.Selection(
        selection=[
            ("carrier", "Carrier obtained price"),
            ("fixed", "Fixed price"),
            ("base_on_rule", "Based on Rules"),
        ],
        default="carrier",
        string="Price method",
    )

    def rate_shipment(self, order):
        """Trick the method for using all the upstream code for the
        price computation in case of using fixed or base_on_rule.

        The method is only swapped in the cache: writing it would lock the
        carrier row and make concurrent transactions fail to serialize.
        """
        if self.price_method not in ("fixed", "base_on_rule"):
            return super().rate_shipment(order)
        field = self._fields["delivery_type"]
        previous_method = self.delivery_type
        self.env.cache.set(self, field, self.price_method)
        try:
            return super().rate_shipment(order)
        finally:
            self.env.cache.set(self, field, previous_method)

    def send_shipping(self, pickings):
        res = super().send_shipping(pickings)
        if self.price_method in ("fixed", "base_on_rule"):
            rates = getattr(self, "%s_send_shipping" % self.price_method)(pickings)
            for index, rate in enumerate(rates):
                del rate["tracking_number"]  # remove offending key
                res[index].update(rate)
        return res
