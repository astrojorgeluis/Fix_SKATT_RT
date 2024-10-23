import argparse
import tkinter as tk
from typing import Optional

import numpy as np
import rtlsdr
from matplotlib.backends.backend_tkagg import (
    FigureCanvasTkAgg,
    NavigationToolbar2Tk,
)
from matplotlib.figure import Figure
from numpy.typing import NDArray
from PIL import Image, ImageTk

from gain_search import find_optimal_gain
from plotting import plot_power_spectrum_on_axes
from record_data import record_power_spectrum
from sdr_wrapper import MockRtlSdr


class TabletopApp:
    def __init__(self, root: tk.Tk, mock_device: bool = False) -> None:
        # The SDR device lass to use
        self._sdr_class = MockRtlSdr if mock_device else rtlsdr.RtlSdr

        # Optimal gain setting found during the preparation step
        self._optimal_gain: Optional[float] = None

        # Baseline power spectrum recorded during the preparation step
        self._baseline_power_spectrum: Optional[NDArray] = None

        self.root = root
        self.init_gui()

    def init_gui(self):
        self.root.title("SKAO Table-top Radio Telescope (TRT) App")

        # Load and display SKAO logo bar at the top
        image_path = "skao_logo_bar.jpg"
        #self.load_and_display_image(image_path)

        # Create Matplotlib Figure
        self.fig = Figure(figsize=(12, 6), dpi=100)
        self.ax = self.fig.add_subplot(111)

        # Create Matplotlib Canvas for Tkinter
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        # Add Matplotlib NavigationToolbar
        self.toolbar = NavigationToolbar2Tk(self.canvas, self.root)
        self.toolbar.update()
        self.canvas.get_tk_widget().pack(side=tk.TOP, fill=tk.BOTH, expand=1)

        # Can call clear_figure(), now that canvas exists
        self.clear_figure()
        self.canvas.draw()

        # Create Status Bar
        font = ("Helvetica", 10)

        self.status_bar = tk.Label(
            self.root,
            text="Status: Ready",
            relief=tk.SUNKEN,
            anchor=tk.W,
            height=2,
            font=font,
        )
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        # Create Buttons
        button_width = 22
        padx = 6

        self.button_plot = tk.Button(
            self.root,
            text="Prepare",
            command=self.prepare,
            width=button_width,
            font=font,
        )
        self.button_plot.pack(side=tk.LEFT, padx=padx)

        self.button_plot = tk.Button(
            self.root,
            text="Observe",
            command=self.sky_obs,
            width=button_width,
            font=font,
        )
        self.button_plot.pack(side=tk.LEFT, padx=padx)

        self.button_plot = tk.Button(
            self.root,
            text="Clear",
            command=self.clear_figure,
            width=button_width,
            font=font,
        )
        self.button_plot.pack(side=tk.LEFT, padx=padx)

        self.button_exit = tk.Button(
            self.root,
            text="Exit",
            command=root.destroy,
            width=button_width,
            font=font,
        )
        self.button_exit.pack(side=tk.LEFT, padx=padx)

        self.show_text_on_figure(
            [
                "Short instruction manual:",
                "1. Prepare",
                "2. Observe",
            ],
            title="SKAO Table-top Radio Telescope (TRT) App",
        )

    def load_and_display_image(self, image_path: str):
        original_image = Image.open(image_path)
        resized_image = original_image.resize((1200, 140))
        tk_image = ImageTk.PhotoImage(resized_image)
        image_label = tk.Label(self.root, image=tk_image, background="white")
        image_label.image = tk_image
        image_label.pack(side=tk.TOP, fill=tk.BOTH, expand=1)

    def clear_figure(self):
        self.ax.clear()
        self.ax.axis("off")
        self.canvas.draw()
        # "Goofy way" to make sure the screen updates
        # https://stackoverflow.com/a/16700254
        self.root.update_idletasks()

    def prepare(self):
        self.show_text_on_figure(
            [
                "This step calibrates your RF device",
                "Searching for optimal gain ...",
            ],
            title="Preparation in progress",
        )

        self.update_status("Finding optimal gain ...")

        try:
            self._optimal_gain = find_optimal_gain(
                self._sdr_class,
                callback=lambda gain: self.update_status(
                    f"Finding optimal gain ... trying gain = {gain:.2f}"
                ),
            )
        except Exception as err:
            self.update_status(f"Preparation failed: {err!s}")
            return

        self.show_text_on_figure(
            [
                "This step calibrates your RF device",
                "Searching for optimal gain ... DONE.",
                "Recording baseline power spectrum ...",
            ],
            title="Preparation in progress",
        )

        # Record baseline integrated power spectrum
        # using optimal gain setting
        self.update_status(
            f"Optimal gain found ({self._optimal_gain:.2f}), "
            "recording baseline power spectrum ..."
        )
        __, self._baseline_power_spectrum = record_power_spectrum(
            self._sdr_class, self._optimal_gain
        )

        self.update_status("Preparation complete!")
        self.show_text_on_figure(
            [
                f"Optimum Gain = {self._optimal_gain:.2f}",
                "You can observe the Milky Way!",
                "Remove RF termination and",
                "Connect your antenna to the Sawbird HI",
            ],
            title="Preparation complete",
        )

    def show_text_on_figure(self, lines: list[str], title: str = ""):
        """
        Display given lines of text on the plotting area. Title is shown at
        the top, in bold and in a different color.
        """
        self.clear_figure()

        SKAO_BLUE = "#070068"
        SKAO_MAGENTA = "#E50869"

        fontsize = 16
        x = 0.12
        y = 0.70
        ystep = 0.1

        self.ax.text(
            x, y, title, fontsize=fontsize, fontweight="bold", color=SKAO_MAGENTA
        )
        y -= ystep

        for line in lines:
            self.ax.text(x, y, line, fontsize=fontsize, color=SKAO_BLUE)
            y -= ystep

        self.canvas.draw()

    def sky_obs(self):
        if self._baseline_power_spectrum is None or self._optimal_gain is None:
            self.update_status("Please run the preparation step first!")
            return

        self.show_text_on_figure(
            [
                "This should take about 30 seconds ...",
                "An interactive graph should appear at the end!",
            ],
            title="Sky observation in progress",
        )
        self.update_status("Recording sky observation ...")

        # Record data, get power spectrum
        print(f"Recording data, using optimal gain: {self._optimal_gain:.2f}")

        try:
            freq_hz, power_spectrum = record_power_spectrum(
                self._sdr_class, self._optimal_gain
            )
        except Exception as err:
            self.update_status(f"Observation failed: {err!s}")
            return

        # Normalise by baseline power spectrum
        HIspectrum = power_spectrum / self._baseline_power_spectrum
        HIspectrum = HIspectrum - np.min(HIspectrum)
        HIspectrum = HIspectrum / np.max(HIspectrum)

        self.update_status("Observation finished!")

        # Plot result
        self.clear_figure()
        plot_power_spectrum_on_axes(self.ax, freq_hz, HIspectrum)
        self.ax.axis("on")  # don't forget to turn axes back on
        self.ax.set_title("Hydrogen Line (HI) signal of the Milky Way", fontsize=16)
        self.ax.set_ylim(np.min(HIspectrum), 1.01)
        self.fig.tight_layout()
        self.canvas.draw()

    def update_status(self, message: str):
        self.status_bar.config(text="Status: " + message)
        # "Goofy way" to make sure the status bar updates
        # https://stackoverflow.com/a/16700254
        self.root.update_idletasks()


def parse_args():
    parser = argparse.ArgumentParser(
        description="Launch the SKAO Tabletop Telescope App"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use a mock version of the SDR device which generates white noise",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    root = tk.Tk()
    root.resizable(True, True)
    app = TabletopApp(root, mock_device=args.mock)
    root.mainloop()
