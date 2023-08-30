import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.colors as mcolors
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from matplotlib import ticker
from datetime import datetime
from PIL import Image
import numpy as np
import re
from scipy import stats
from scipy.interpolate import UnivariateSpline
import statsmodels.api as sm


from IR_api_handler import IR_Handler

iracing_api = IR_Handler()
from itertools import cycle


def ms_to_laptime(ms):
    total_secs = ms / 10000  # this is not ms but 1/10000th of a second
    minutes = int(total_secs // 60)
    seconds = int(total_secs % 60)
    remaining_ms = int(ms % 1000)
    return f"{minutes}:{seconds:02d}.{remaining_ms:03d}"


bar_color_grad = [
    "#2cbdfe",
    "#2fb9fc",
    "#33b4fa",
    "#36b0f8",
    "#3aacf6",
    "#3da8f4",
    "#41a3f2",
    "#449ff0",
    "#489bee",
    "#4b97ec",
    "#4f92ea",
    "#528ee8",
    "#568ae6",
    "#5986e4",
    "#5c81e2",
    "#607de0",
    "#6379de",
    "#6775dc",
    "#6a70da",
    "#6e6cd8",
    "#7168d7",
    "#7564d5",
    "#785fd3",
    "#7c5bd1",
    "#7f57cf",
    "#8353cd",
    "#864ecb",
    "#894ac9",
    "#8d46c7",
    "#9042c5",
    "#943dc3",
    "#9739c1",
    "#9b35bf",
    "#9e31bd",
    "#a22cbb",
    "#a528b9",
    "#a924b7",
    "#ac20b5",
    "#b01bb3",
    "#b317b1",
]


import os
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from matplotlib.offsetbox import OffsetImage, AnnotationBbox

import os
import matplotlib.pyplot as plt
import numpy as np
from PIL import Image
from matplotlib.offsetbox import OffsetImage, AnnotationBbox


def bar_graph_recentincidents(data, bar_color="#30a2da", logo_path="./images/srd.png"):
    """
    Plots a bar graph of recent incidents per driver and saves the output to an image file.

    Args:
    data: A dictionary where keys are driver names and values are the corresponding number of recent incidents.
    cmap_name: The name of the color map to use. Default is 'viridis'.
    logo_path: The file path to the logo to be displayed in the plot. Default is './images/srd.png'.
    """
    plt.style.use("fivethirtyeight")
    plt.clf()

    driver_names = list(data.keys())
    recent_incidents = list(data.values())

    if min(recent_incidents) == max(recent_incidents):
        colors = [plt.get_cmap("Blues")(0.5) for _ in recent_incidents]  # middle shade of blue
    else:
        # Configure color map
        cmap = plt.get_cmap("Blues")
        norm = plt.Normalize(min(recent_incidents), max(recent_incidents))
        colors = cmap(norm(recent_incidents))

    # Plot bar chart
    bars = plt.bar(driver_names, recent_incidents, color=colors)
    for bar in bars:
        y_val = bar.get_height()
        plt.text(
            bar.get_x() + bar.get_width() / 2,
            y_val,
            int(y_val),
            va="bottom",
            ha="center",
            color="black",
        )

    # Configure labels and title
    plt.xlabel("Driver Name", weight="bold")
    plt.ylabel("Recent Incidents", weight="bold")
    plt.title("Recent Incidents per Driver")

    # Add logo to the plot
    logo_img = Image.open(logo_path)
    logo_array = np.array(logo_img)
    imagebox = OffsetImage(logo_array, zoom=0.1)
    #ab = AnnotationBbox(imagebox, (0, 1), frameon=False, pad=0)
    #plt.gca().add_artist(ab)

    # Configure additional plot settings
    plt.gca().set_facecolor("none")
    plt.tick_params(axis="both", which="major", labelsize="large", width=2, length=6)
    plt.gca().xaxis.label.set_weight("bold")
    plt.gca().yaxis.label.set_weight("bold")

    # Save the plot as a .png image
    output_path = os.path.join(".", "images", "incidents.png")
    plt.savefig(output_path)
    plt.close()


def line_chart_irating(data, start_date_str=None, end_date_str=None):
    plt.figure(figsize=(15, 10))
    plt.style.use("fivethirtyeight")  # Using dark theme

    date_pattern = re.compile(r"\d{4}-\d{2}-\d{2}")

    for driver_name, driver_data in data.items():
        dates = []
        iratings = []
        for d in driver_data["data"]:
            if date_pattern.match(d["when"]):
                dates.append(datetime.strptime(d["when"], "%Y-%m-%d"))
                iratings.append(d["value"])
            else:
                print(f"Incorrect date format for {d['when']}, skipped")

        # Filter data if dates are provided
        if start_date_str is not None or end_date_str is not None:
            start_date = (
                datetime.strptime(start_date_str, "%Y-%m-%d")
                if start_date_str
                else min(dates)
            )
            end_date = (
                datetime.strptime(end_date_str, "%Y-%m-%d")
                if end_date_str
                else max(dates)
            )
            indices = [
                i
                for i, date in enumerate(dates)
                if date >= start_date and date <= end_date
            ]
            dates = [dates[i] for i in indices]
            iratings = [iratings[i] for i in indices]

        plt.plot(
            dates, iratings, label=driver_name
        )  # Plot line for each driver and add driver's name as a label

    plt.gca().xaxis.set_major_locator(
        mdates.DayLocator(interval=30)
    )  # Sets ticks at every 10th day
    plt.gca().xaxis.set_major_formatter(
        mdates.DateFormatter("%Y-%m-%d")
    )  # Format dates in the form 'YYYY-mm-dd'
    plt.gcf().autofmt_xdate()  # Autoformats the date labels (try to fit as many as possible etc.)
    plt.title("iRating History", fontsize=14)

    img = Image.open("./images/srd.png")
    logo = np.array(img)  # Convert the image to a numpy array

    # Display the image on the plot
    imagebox = OffsetImage(logo, zoom=0)  # Change zoom level to resize the logo
    ab = AnnotationBbox(
        imagebox, (0.2, -0.5), frameon=False, pad=1
    )  # The coordinates (0.9, 0.9) place the logo at the top-right corner. Adjust as necessary.

    plt.xlabel("Date", fontsize=14, weight="bold")
    plt.ylabel("iRating", fontsize=14, weight="bold")
    plt.yticks(fontsize=12)
    plt.xticks(fontsize=12, rotation=90)
    plt.legend()  # Display legend
    plt.grid(True)

    plt.gca().add_artist(ab)
    plt.gca().set_facecolor("none")

    plt.savefig("./images/driver_irating.png")
    plt.close()


def line_chart_laps(data):
    plt.figure(figsize=(15, 10))
    plt.style.use("fivethirtyeight")

    lap_numbers = list(data.keys())
    lap_times = list(data.values())

    if len(lap_numbers) < 2 or len(lap_times) < 2:
        raise ValueError("Data must contain at least two laps")

    # Calculate and plot the trendline excluding the first lap
    x = np.array(lap_numbers[1:])  # exclude the first lap
    y = np.array(lap_times[1:])  # exclude the first lap time
    z = np.polyfit(x, y, 1)
    p = np.poly1d(z)
    plt.plot(x, p(x), "r--")  # plot trendline

    plt.plot(lap_numbers[1:], lap_times[1:], marker="o")

    plt.title("Lap Times", fontsize=14, weight="bold")
    plt.xlabel("Lap Number", fontsize=14, weight="bold")
    plt.ylabel("Lap Time", fontsize=14, weight="bold")
    plt.yticks(fontsize=12)
    plt.xticks(
        np.arange(min(lap_numbers), max(lap_numbers) + 1, 1.0), fontsize=12, rotation=90
    )

    plt.legend(["Trendline (Excluding First Lap)", "Lap Time"])  # Display legend
    plt.grid(True)

    ax = plt.gca()  # get the current axes
    formatter = ticker.FuncFormatter(lambda ms, x: ms_to_laptime(ms))

    # Set y-ticks to be exactly at the data points
    y_ticks = np.unique(lap_times[1:])  # exclude the first lap time
    ax.set_yticks(y_ticks)
    ax.yaxis.set_major_formatter(formatter)

    # Fit a simple linear regression model
    X = sm.add_constant(x)
    model = sm.OLS(y, X)
    results = model.fit()

    if len(results.params) > 1:
        coef_str = "Coef.: {:.3f}".format(results.params[1])
    else:
        coef_str = "Coef. is not available"
    if len(results.pvalues) > 1:
        pvalue_str = "p-value: {:.3f}".format(results.pvalues[1])
    else:
        pvalue_str = "p-value is not available"

    # Determine consistency based on p-value and coefficient
    pvalue_threshold = 2  # define your p-value threshold
    coef_threshold = 5000  # define your coefficient threshold (this is an example, adjust based on your context)

    # if results.pvalues[1] <= pvalue_threshold and abs(results.params[1]) > coef_threshold:
    #    consistency = 'consistent'
    # else:
    #    consistency = 'inconsistent'
    #
    # consistency_str = f'Consistency: {consistency}'

    ax.text(
        0.95,
        0.95,
        coef_str + "\n" + pvalue_str + "\n",
        transform=ax.transAxes,
        verticalalignment="top",
        horizontalalignment="right",
    )  # noqa: E501

    plt.savefig("./images/line_chart_laps.png")
    plt.close()


def line_chart_race_position(data):
    data.sort(key=lambda x: x["lap_number"])
    # Group the data by driver
    drivers = {}
    num_lines = 20  # or however many lines you have
    colors = plt.get_cmap("tab10", num_lines)

    for item in data:
        if item["display_name"] not in drivers:
            drivers[item["display_name"]] = []
        drivers[item["display_name"]].append(item["lap_position"])
    fig = plt.figure(figsize=(20, 10))
    ax1 = fig.add_subplot(111)
    # plt.style.use('fivethirtyeight')
    for i, (driver, positions) in enumerate(drivers.items()):
        (line,) = plt.plot(
            positions, color=colors(i % 10), label=driver, linestyle="-", marker="o"
        )
        mid_x = len(positions) // 2
        mid_y = positions[mid_x]
        plt.text(
            mid_x, mid_y, driver, color=line.get_color(), weight="semibold", fontsize=10
        )

    plt.tight_layout()
    lgd = plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left", borderaxespad=0.0)
    ax1.set_xlabel("Lap Number", fontsize=14, weight="bold")
    ax1.set_ylabel("Position", fontsize=14, weight="bold")
    max_lap = max(len(positions) for positions in drivers.values())

    # Set the xticks to show every lap
    plt.xticks(np.arange(0, max_lap, 1))

    # Make y-axis intervals of 1
    y_max = max(max(pos) for pos in drivers.values())
    y_min = min(min(pos) for pos in drivers.values())
    ax1.set_yticks(range(1, y_max + 1))
    ax1.tick_params(axis="y", labelsize=12)

    # Invert y-axis
    # ax1.invert_yaxis()

    # Create a second y-axis on the right side
    ax2 = ax1.twinx()
    ax2.set_ylabel("Position", fontsize=14, weight="bold")
    ax2.set_yticks(range(1, y_max + 1))
    ax2.tick_params(axis="y", labelsize=12)
    ax1.invert_yaxis()
    ax2.invert_yaxis()

    plt.title("Driver Position through Race", fontsize=14, weight="bold")
    plt.tight_layout()
    plt.savefig(
        "./images/race_position_line.png",
        bbox_inches="tight",
        bbox_extra_artists=(lgd,),
    )


def line_chart_race_position_interpolate(data):
    data.sort(key=lambda x: x["lap_number"])
    # Group the data by driver
    drivers = {}
    num_lines = 20  # or however many lines you have
    colors = plt.get_cmap("tab10", num_lines)

    for item in data:
        if item["display_name"] not in drivers:
            drivers[item["display_name"]] = []
        drivers[item["display_name"]].append(item["lap_position"])

    fig = plt.figure(figsize=(20, 10))
    ax1 = fig.add_subplot(111)

    for i, (driver, positions) in enumerate(drivers.items()):
        x = np.array(list(range(len(positions))))
        y = np.array(positions)

        if len(x) > 3 and len(y) > 3:  # spline fitting requires more than 3 data points
            spl = UnivariateSpline(x, y)
            xnew = np.linspace(0, len(positions) - 1, 1000)
            y_smooth = spl(xnew)
            (line,) = ax1.plot(
                xnew, y_smooth, color=colors(i % num_lines), label=driver
            )
            mid_x = xnew[
                len(xnew) // 2
            ]  # calculate the mid-point of the new, smoother line
            mid_y = y_smooth[len(y_smooth) // 2]
            ax1.text(
                mid_x,
                mid_y,
                driver,
                color=line.get_color(),
                weight="semibold",
                fontsize=10,
            )

    plt.tight_layout()
    lgd = plt.legend(bbox_to_anchor=(1.05, 1), loc="upper left", borderaxespad=0.0)
    ax1.set_xlabel("Lap Number", fontsize=14, weight="bold")
    ax1.set_ylabel("Position", fontsize=14, weight="bold")
    max_lap = max(len(positions) for positions in drivers.values())

    # Set the xticks to show every lap
    plt.xticks(np.arange(0, max_lap, 1))

    # Make y-axis intervals of 1
    y_max = max(max(pos) for pos in drivers.values())
    y_min = min(min(pos) for pos in drivers.values())
    ax1.set_yticks(range(1, y_max + 1))
    ax1.tick_params(axis="y", labelsize=12)

    # Invert y-axis
    # ax1.invert_yaxis()

    # Create a second y-axis on the right side
    ax2 = ax1.twinx()
    ax2.set_ylabel("Position", fontsize=14, weight="bold")
    ax2.set_yticks(range(1, y_max + 1))
    ax2.tick_params(axis="y", labelsize=12)
    ax1.invert_yaxis()
    ax2.invert_yaxis()

    plt.title("Driver Position through Race", fontsize=14, weight="bold")
    plt.tight_layout()
    plt.savefig(
        "./images/race_position_line_interpolate.png",
        bbox_inches="tight",
        bbox_extra_artists=(lgd,),
    )

def recentraces_trendline(races_data):
    finish_positions = [race['finish_position'] for race in races_data]
    if finish_positions[-1] < finish_positions[0]:
        trend = "Getting better..."
    elif finish_positions[-1] > finish_positions[0]:
        trend = "Getting worse..."
    else:
        trend = "Stuck in a rut..."
    plt.figure(figsize=(10,6))
    plt.style.use("fivethirtyeight")
    plt.plot(finish_positions, '-o', label='Finish Position')
    plt.gca().invert_yaxis()  # Lower finish positions (e.g., 1st) are better
    plt.title(f"Race Finish Positions: {trend}")
    plt.xlabel('Race')
    plt.ylabel('Finish Position')
    plt.legend()
    plt.grid(True, which='both', linestyle='--', linewidth=0.5)
    image_path = "./images/recentraces_trend.png"
    plt.savefig(image_path)
    plt.close()
    return image_path
    