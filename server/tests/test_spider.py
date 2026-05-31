import json
from spider import format_dict_for_prompt


class TestFormatDictForPrompt:
    def test_invalid_json_returns_raw(self):
        assert format_dict_for_prompt("not json") == "not json"

    def test_empty_dict(self):
        result = format_dict_for_prompt("{}")
        assert result == ""

    def test_basic_explanation_only(self):
        data = json.dumps(
            {
                "basic_explanation": [
                    {"brief": "代词：这、此"},
                    {"brief": "连词：表示顺承", "examples": ["例一", "例二"]},
                ]
            }
        )
        result = format_dict_for_prompt(data)
        assert "【基本解释】" in result
        assert "代词：这、此" in result
        assert "连词：表示顺承" in result
        assert "例一" in result
        assert "例二" in result
        assert "【详细解释】" not in result

    def test_detailed_explanation_with_pos_and_english(self):
        data = json.dumps(
            {
                "detailed_explanation": [
                    {
                        "brief": "用在动词前",
                        "pos": "助词",
                        "english": "used before a verb",
                        "citations": ["《论语》——学而时习之"],
                        "examples": ["学而时习之"],
                    }
                ]
            }
        )
        result = format_dict_for_prompt(data)
        assert "【详细解释】" in result
        assert "用在动词前" in result
        assert "[助词]" in result
        assert "[used before a verb]" in result
        assert "书证：《论语》——学而时习之" in result
        assert "例：学而时习之" in result
        assert "【基本解释】" not in result

    def test_detailed_explanation_with_citations_only(self):
        data = json.dumps(
            {
                "detailed_explanation": [
                    {
                        "brief": "指示代词",
                        "citations": ["此——《诗经》"],
                    }
                ]
            }
        )
        result = format_dict_for_prompt(data)
        assert "指示代词" in result
        assert "书证：此——《诗经》" in result

    def test_old_schema_examples_fallback(self):
        data = json.dumps(
            {
                "detailed_explanation": [
                    {
                        "brief": "旧义项",
                        "examples": ["旧例"],
                    }
                ]
            }
        )
        result = format_dict_for_prompt(data)
        assert "旧义项" in result
        assert "例：旧例" in result

    def test_both_sections(self):
        data = json.dumps(
            {
                "basic_explanation": [{"brief": "基本义"}],
                "detailed_explanation": [{"brief": "详细义"}],
            }
        )
        result = format_dict_for_prompt(data)
        assert "【基本解释】" in result
        assert "【详细解释】" in result
        assert "基本义" in result
        assert "详细义" in result


CHAR_HTML = """<div class="char-card">
  <div class="char-card__main">
    <div class="char-meta">
      <span class="meta-pinyin">zhī</span>
      <span class="meta-pinyin">zhì</span>
      <span class="meta-zhuyin">ㄓ</span>
      <span class="meta-radical">丶</span>
      <span class="meta-badge">总笔画</span><span>3</span>
    </div>
  </div>
</div>
<div id="jbjs">
  <div class="jbjs-item">
    <div class="jbjs-item__def">代词：这、此</div>
    <div class="jbjs-item__eg">之乎者也</div>
  </div>
</div>
<div id="xxjs">
  <div class="xxjs-pos-section">
    <span class="xxjs-pos-badge">助词</span>
    <div class="xxjs-item">
      <div class="xxjs-item__def">用在动词前</div>
      <div class="xxjs-citation__item">
        <span class="xxjs-citation__text">学而时习之</span>
        <span class="xxjs-citation__source">《论语》</span>
      </div>
      <div class="xxjs-english"><span class="xxjs-english__text">it</span></div>
    </div>
  </div>
</div>"""


class TestParseCharSection:
    def test_parse_full_char(self):
        from bs4 import BeautifulSoup
        from spider import _parse_char_section

        soup = BeautifulSoup(CHAR_HTML, "html.parser")
        result = _parse_char_section(soup)
        assert result["pinyin"] == ["zhī", "zhì"]
        assert result["zhuyin"] == ["ㄓ"]
        assert result["radical"] == "丶"
        assert result["strokes"] == 3
        assert len(result["basic_explanation"]) == 1
        assert result["basic_explanation"][0]["brief"] == "代词：这、此"
        assert result["basic_explanation"][0]["examples"] == ["之乎者也"]
        assert len(result["detailed_explanation"]) == 1
        assert result["detailed_explanation"][0]["brief"] == "用在动词前"
        assert result["detailed_explanation"][0]["pos"] == "助词"
        assert result["detailed_explanation"][0]["english"] == "it"
        assert len(result["detailed_explanation"][0]["citations"]) == 1
        assert "学而时习之" in result["detailed_explanation"][0]["citations"][0]

    def test_parse_empty_char(self):
        from bs4 import BeautifulSoup
        from spider import _parse_char_section

        soup = BeautifulSoup("<div></div>", "html.parser")
        result = _parse_char_section(soup)
        assert result["pinyin"] == []
        assert result["zhuyin"] == []
        assert result["radical"] == ""
        assert result["strokes"] == 0
        assert result["basic_explanation"] == []
        assert result["detailed_explanation"] == []


WORD_HTML = """<div class="word-headword-row">明府</div>
<div class="word-pronun-text">
  <span class="meta-pinyin">míng fǔ</span>
</div>
<div id="xxjs">
  <div class="xxjs-item">
    <div class="xxjs-item__def">旧时对地方官员的尊称</div>
    <div class="xxjs-citation__item">
      <span class="xxjs-citation__text">明府，官也</span>
      <span class="xxjs-citation__source">《后汉书》</span>
    </div>
  </div>
</div>"""


class TestParseWordSection:
    def test_parse_full_word(self):
        from bs4 import BeautifulSoup
        from spider import _parse_word_section

        soup = BeautifulSoup(WORD_HTML, "html.parser")
        result = _parse_word_section(soup)
        assert result["word"] == "明府"
        assert result["pinyin"] == ["míng fǔ"]
        assert len(result["detailed_explanation"]) == 1
        assert result["detailed_explanation"][0]["brief"] == "旧时对地方官员的尊称"
        assert "明府，官也" in result["detailed_explanation"][0]["citations"][0]

    def test_parse_empty_word(self):
        from bs4 import BeautifulSoup
        from spider import _parse_word_section

        soup = BeautifulSoup("<div></div>", "html.parser")
        result = _parse_word_section(soup)
        assert result["word"] == ""
        assert result["pinyin"] == []
        assert result["basic_explanation"] == []
        assert result["detailed_explanation"] == []


class TestParseZdicHtml:
    def test_parse_char_html(self):
        from spider import parse_zdic_html

        result = parse_zdic_html(CHAR_HTML)
        assert result is not None
        assert result["pinyin"] == ["zhī", "zhì"]

    def test_parse_word_html(self):
        from spider import parse_zdic_html

        result = parse_zdic_html(WORD_HTML)
        assert result is not None
        assert result["word"] == "明府"

    def test_parse_404_html(self):
        from spider import parse_zdic_html

        result = parse_zdic_html("<html><body>404 Not Found</body></html>")
        assert result is None
