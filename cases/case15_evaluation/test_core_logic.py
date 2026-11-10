"""
第一层测试：纯逻辑，不碰模型。秒级运行，每次改代码都该跑。
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from cases.case15_evaluation.core import calc_shipping_fee


def test_free_shipping_at_threshold():
    assert calc_shipping_fee(99) == 0.0


def test_free_shipping_above_threshold():
    assert calc_shipping_fee(150) == 0.0


def test_charges_fee_below_threshold():
    assert calc_shipping_fee(50) == 8.0


def test_charges_fee_at_boundary_minus_one():
    assert calc_shipping_fee(98.99) == 8.0
