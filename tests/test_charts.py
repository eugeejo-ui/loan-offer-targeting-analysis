from charts import channel_of, pretty_segment


def test_pretty_segment_rewrites_amount_band_and_channel():
    assert pretty_segment("(599.999, 6500.0] | 신규·A_Submitted | Car") == "6,500 이하 · 신규·A_Submitted 있음 · Car"
    assert pretty_segment("(25000.0, 450000.0] | 한도 증액") == "25,000 초과 · 한도 증액"
    assert pretty_segment("0 (미기재) | 신규·표식 없음 | 용도 불명") == "금액 미기재 · 신규·A_Submitted 없음 · 용도 불명"


def test_channel_of_keeps_internal_label():
    assert channel_of("(10000.0, 15500.0] | 신규·표식 없음") == "신규·표식 없음"
    assert channel_of("(599.999, 6500.0] | 기타") == "기타"
