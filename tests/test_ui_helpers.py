
from unittest.mock import patch

from utils.ui_helpers import render_resource_links


def test_resource_links_accept_valid_https_urls():
    with patch("utils.ui_helpers.st") as mock_st:
        render_resource_links(
            [
                "https://docs.python.org/3/tutorial/",
                "https://learn.microsoft.com/power-bi/",
            ]
        )

    assert mock_st.link_button.call_count == 2


def test_resource_links_reject_http_urls():
    with patch("utils.ui_helpers.st") as mock_st:
        render_resource_links(["http://example.com"])

    mock_st.link_button.assert_not_called()
    mock_st.caption.assert_called_once()


def test_resource_links_reject_javascript_urls():
    with patch("utils.ui_helpers.st") as mock_st:
        render_resource_links(["javascript:alert(1)"])

    mock_st.link_button.assert_not_called()


def test_resource_links_reject_urls_without_hostname():
    with patch("utils.ui_helpers.st") as mock_st:
        render_resource_links(["https:///"])

    mock_st.link_button.assert_not_called()


def test_resource_links_reject_embedded_credentials():
    with patch("utils.ui_helpers.st") as mock_st:
        render_resource_links(["https://user:password@example.com"])

    mock_st.link_button.assert_not_called()


def test_resource_links_ignore_non_string_values():
    with patch("utils.ui_helpers.st") as mock_st:
        render_resource_links([None, 123, "https://docs.python.org/"])

    mock_st.link_button.assert_called_once()


def test_resource_links_handle_empty_list():
    with patch("utils.ui_helpers.st") as mock_st:
        render_resource_links([])

    mock_st.caption.assert_called_once()
    mock_st.link_button.assert_not_called()
