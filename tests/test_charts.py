from charts import channel_of, pretty_segment


def test_pretty_segment_names_each_axis_in_plain_korean():
    assert pretty_segment("(599.999, 6500.0] | 신규·A_Submitted 있음 | Car") == "소액 · 신규(표식 있음) · 자동차 구입"
    assert pretty_segment("(10000.0, 15500.0] | 신규·A_Submitted 없음 | Existing loan takeover") == \
        "중액 · 신규(표식 없음) · 대출 대환"
    assert pretty_segment("금액 미기재 | 신규·A_Submitted 없음 | 용도 불명") == "금액 미기재 · 신규(표식 없음) · 용도 미기재"
    assert pretty_segment("(15500.0, 25000.0] | 신규·A_Submitted 있음 | 기타") == "고액 · 신규(표식 있음) · 그 외 용도"
    # 경로 축의 잔여 셀과 용도 축의 잔여 셀은 다른 것이므로 이름도 다르다
    assert pretty_segment("(599.999, 6500.0] | 기타") == "소액 · 그 외 경로 · 용도 전체"


def test_pretty_segment_fills_the_missing_purpose_axis():
    assert pretty_segment("(25000.0, 450000.0] | 한도 증액") == "초고액 · 한도 증액 · 용도 전체"


def test_channel_of_keeps_internal_label():
    assert channel_of("(10000.0, 15500.0] | 신규·A_Submitted 없음") == "신규·A_Submitted 없음"
    assert channel_of("(599.999, 6500.0] | 기타") == "기타"
