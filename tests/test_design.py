from design import ab_sample_size


def test_ab_sample_size_known_value():
    # p1 = 0.5 → p2 = 0.6, alpha 0.05 two-sided, power 0.8: 387.3 → 388 per arm
    assert ab_sample_size(0.5, 0.1) == 388
    assert ab_sample_size(0.5, -0.1) == ab_sample_size(0.4, 0.1)
