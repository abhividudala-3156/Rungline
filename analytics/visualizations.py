import pandas as pd
import plotly.express as px


def competency_gap_chart(rows):
    data = [r for r in rows if r.get("current_level") is not None]
    if not data:
        return None
    frame = pd.DataFrame(data)
    long = frame.melt(
        id_vars=["name"],
        value_vars=["required_level", "current_level"],
        var_name="measure",
        value_name="level",
    )
    return px.bar(
        long,
        x="name",
        y="level",
        color="measure",
        barmode="group",
        title="Current competency vs career requirement",
        range_y=[0, 5],
    )


def progress_chart(progress_records):
    if not progress_records:
        return None
    frame = pd.DataFrame(progress_records)
    frame["status"] = frame["completed"].map({True: "Completed", False: "In progress"})
    return px.pie(frame, names="status", title="Learning activity progress")
