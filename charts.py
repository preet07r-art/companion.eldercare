import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# This file contains all chart drawing functions.
# Each function draws one chart and ends with st.pyplot(fig) and plt.close().

def draw_bmi_gauge(bmi_value, dot_color):
    # Draws a horizontal BMI scale bar with a colored dot at the user's BMI value
    fig, ax = plt.subplots(figsize=(6, 0.6))

    # Draw four colored zones on the scale
    ax.barh([0], [18.5], color="blue",   alpha=0.3, label="Underweight")
    ax.barh([0], [6.4],  left=18.5, color="green",  alpha=0.4, label="Normal")
    ax.barh([0], [5.0],  left=24.9, color="orange", alpha=0.4, label="Overweight")
    ax.barh([0], [10.1], left=29.9, color="red",    alpha=0.4, label="Obese")

    # Draw a dot at the user's BMI value
    ax.scatter([bmi_value], [0], color=dot_color, s=200, zorder=5)
    ax.set_xlim(10, 40)
    ax.set_yticks([])
    ax.set_xlabel("BMI Scale")

    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

def draw_line_chart(dates, values, title, y_label, line_color="blue"):
    # Draws a simple line chart for a list of (date, value) pairs
    fig, ax = plt.subplots(figsize=(7, 3.5))

    ax.plot(dates, values, color=line_color, marker="o", markersize=4)
    ax.set_title(title, fontsize=10)
    ax.set_ylabel(y_label, fontsize=9)

    plt.xticks(rotation=45, fontsize=8)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

def draw_two_lines(dates, values1, values2, label1, label2, title, y_label):
    # Draws a line chart with two lines — for example Before and After Meal sugar
    fig, ax = plt.subplots(figsize=(7, 3.5))

    ax.plot(dates, values1, color="blue",  marker="o", markersize=4, label=label1)
    ax.plot(dates, values2, color="red",   marker="s", markersize=4, label=label2)
    ax.set_title(title, fontsize=10)
    ax.set_ylabel(y_label, fontsize=9)
    ax.legend(fontsize=8)

    plt.xticks(rotation=45, fontsize=8)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

def draw_bar_chart(labels, taken_values, missed_values, title):
    # Draws a grouped bar chart comparing Taken vs Missed doses per day
    x = np.arange(len(labels))
    width = 0.35

    fig, ax = plt.subplots(figsize=(7, 3.5))
    ax.bar(x - width/2, taken_values,  width, label="Taken",  color="#2ecc71")
    ax.bar(x + width/2, missed_values, width, label="Missed", color="#e74c3c")

    ax.set_title(title, fontsize=10)
    ax.set_ylabel("Number of Doses", fontsize=9)
    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=8, rotation=45)
    ax.legend(fontsize=8)

    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

def draw_heatmap(data_frame, title, show_numbers=True):
    # Draws a Seaborn heatmap — green means doses taken, red means missed
    fig, ax = plt.subplots(figsize=(max(5, len(data_frame.columns) * 0.4),
                                    max(2, len(data_frame) * 0.5)))

    sns.heatmap(data_frame, annot=show_numbers, fmt=".0f",
                cmap="RdYlGn", cbar=False, linewidths=0.5,
                ax=ax, annot_kws={"size": 8})

    ax.set_title(title, fontsize=10)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

def draw_violin_plot(data_frame, column_list, title):
    # Draws a Seaborn violin plot showing how much vitals readings vary
    import pandas as pd
    melted = data_frame.melt(value_vars=column_list)

    fig, ax = plt.subplots(figsize=(7, 3))
    sns.violinplot(data=melted, x="variable", y="value",
                   palette="pastel", inner="quart", ax=ax)

    ax.set_title(title, fontsize=10)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

def draw_comparison_bars(metric_names, this_week_values, last_week_values, title):
    # Draws a grouped bar chart to compare this week vs last week for each vital
    x = np.arange(len(metric_names))
    width = 0.35

    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.bar(x - width/2, this_week_values, width, label="This Week", color="#3498db")
    ax.bar(x + width/2, last_week_values, width, label="Last Week", color="#95a5a6")

    ax.set_title(title, fontsize=10)
    ax.set_xticks(x)
    ax.set_xticklabels(metric_names, fontsize=8)
    ax.legend(fontsize=8)

    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)

def draw_goal_gauges(latest_vitals, goals):
    # Draws simple horizontal bars showing if current vitals are within goal range
    # latest_vitals is a dictionary with keys like 'Systolic', 'Diastolic', etc.
    metrics = [
        ("Systolic",  "bp_systolic_min",  "bp_systolic_max",  "#3498db"),
        ("Diastolic", "bp_diastolic_min", "bp_diastolic_max", "#2ecc71"),
        ("Heart Rate", "heart_rate_min",  "heart_rate_max",  "#e67e22")
    ]
    
    fig, ax = plt.subplots(figsize=(7, 2.5))
    for i, (name, min_key, max_key, bar_color) in enumerate(metrics):
        val = latest_vitals.get(name, 0)
        mn  = float(goals.get(min_key, 0))
        mx  = float(goals.get(max_key, 200))
        
        # Draw background goal range as a light bar
        ax.barh(i, mx - mn, left=mn, color=bar_color, alpha=0.2)
        # Draw current value as a thick vertical marker
        ax.vlines(val, i - 0.3, i + 0.3, color=bar_color, linewidth=4)
        ax.text(val, i + 0.1, f" {val}", color=bar_color, fontweight='bold', fontsize=9)
    
    ax.set_yticks(range(len(metrics)))
    ax.set_yticklabels([m[0] for m in metrics], fontsize=9)
    ax.set_title("Latest Readings vs Goal Ranges", fontsize=10)
    plt.tight_layout()
    st.pyplot(fig)
    plt.close(fig)
