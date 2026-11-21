
from urllib.parse import urlsplit

import streamlit as st


def render_competency_scores(skill_scores, title="Competency Scores"):
    """Display competency scores as readable metric cards and progress bars."""

    st.subheader(title)

    if not skill_scores:
        st.info(
            "No competency scores are available yet. Complete an assessment first."
        )
        return

    items = []

    for skill, score in skill_scores.items():
        try:
            score = float(score)
        except (TypeError, ValueError):
            continue

        score = max(0.0, min(100.0, score))
        items.append((skill, score))

    if not items:
        st.info("No valid competency scores are available.")
        return

    columns_per_row = 3

    for start in range(0, len(items), columns_per_row):
        columns = st.columns(columns_per_row)

        for column, (skill, score) in zip(
            columns, items[start : start + columns_per_row]
        ):
            with column:
                st.metric(skill.replace("_", " ").title(), f"{score:.0f}%")
                st.progress(score / 100)

                if score >= 80:
                    st.caption("Strong performance")
                elif score >= 50:
                    st.caption("Developing competency")
                else:
                    st.caption("Needs improvement")


def render_recommendations(summary, recommendations):
    """Display AI recommendations as plain text."""

    st.subheader("AI Learning Recommendations")

    if summary:
        st.text(summary)

    if recommendations:
        for index, recommendation in enumerate(recommendations, start=1):
            st.text(f"{index}. {recommendation}")
    else:
        st.caption("No additional recommendations are available.")


def render_learning_activities(activities):
    """Display learning activities as plain text."""

    if not activities:
        st.caption("No specific activities were provided.")
        return

    for index, activity in enumerate(activities, start=1):
        st.text(f"{index}. {activity}")


def render_resource_links(urls):
    """Display only valid HTTPS resource links."""

    if not urls:
        st.caption("No external resources provided.")
        return

    safe_urls = []

    for url in urls:
        if not isinstance(url, str):
            continue

        try:
            parsed = urlsplit(url.strip())

            if (
                parsed.scheme == "https"
                and parsed.hostname
                and not parsed.username
                and not parsed.password
            ):
                safe_urls.append(url.strip())

        except ValueError:
            continue

    if not safe_urls:
        st.caption("No valid HTTPS resources available.")
        return

    st.markdown("**Learning Resources**")

    for index, url in enumerate(safe_urls, start=1):
        st.link_button(f"Open learning resource {index}", url)
