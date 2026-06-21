from app.scenario.loader import load_scenario, strip_hidden_sections

SCENARIO = "saver-studio"


def test_strip_hidden_sections_removes_marked_and_keeps_rest():
    md = (
        "# 제목\n\n## 보이는 섹션\n내용A\n\n"
        "## 정답 키(비노출)\n비밀1\n비밀2\n\n"
        "## 또 보이는 섹션\n내용B\n"
    )
    out = strip_hidden_sections(md)
    assert "내용A" in out
    assert "내용B" in out
    assert "비밀1" not in out and "비밀2" not in out
    assert "정답 키" not in out


def test_load_scenario_exposes_user_facing_only():
    b = load_scenario(SCENARIO)
    assert b.scenario_id == SCENARIO
    assert b.background  # 배경 존재
    assert "갱신" in b.task_message  # 매니저 과제 인용
    ids = {p.persona_id for p in b.personas}
    assert ids == {
        "manager-kim-dohyun",
        "customer-park-sangwoo",
        "engineer-lee-seoyeon",
    }
    assert all(p.name and p.role for p in b.personas)


def test_assets_present_but_answer_key_stripped():
    b = load_scenario(SCENARIO)
    # CSV 그대로 노출(헤더 포함)
    assert "conversation_id" in b.cs_logs_csv
    # 대시보드의 비노출(채점·골든셋용) 섹션은 제거
    assert "읽어내야 할 신호" not in b.dashboard_md
    assert "사용자 비노출" not in b.dashboard_md
    # 그래도 실제 표/수치는 남아 있어야 함
    assert "CSAT" in b.dashboard_md
