from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import cv2
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure


DEFAULT_IMAGE = Path(__file__).resolve().parents[1] / "data" / "imageBW.png" #importはこの行で行う


def read_grayscale(path):
    """Read an image, including paths containing non-ASCII characters."""
    encoded = np.fromfile(str(path), dtype=np.uint8)
    image = cv2.imdecode(encoded, cv2.IMREAD_GRAYSCALE)
    if image is None:
        raise ValueError(f"Cannot read image: {path}")
    return image


def minmax_stretch(image, out_min=0, out_max=255):
    in_min = int(np.min(image))
    in_max = int(np.max(image))
    if in_max == in_min:
        return np.full_like(image, out_min)
    stretched = (image.astype(np.float32) - in_min) * \
                (out_max - out_min) / (in_max - in_min) + out_min
    return np.clip(stretched, out_min, out_max).astype(np.uint8)


def analyze_image(image):
    """Run the variant-4 contrast enhancement and point/line/edge methods."""
    if image is None or image.ndim != 2 or image.size == 0:
        raise ValueError("Expected a non-empty grayscale image.")

    stretched = minmax_stretch(image)
    equalized = cv2.equalizeHist(image)

    laplacian = cv2.Laplacian(image, cv2.CV_32F, ksize=3)
    point_response = np.abs(laplacian)
    point_threshold = max(30.0, float(np.percentile(point_response, 99.5)))
    points = cv2.threshold(
        point_response, point_threshold, 255, cv2.THRESH_BINARY
    )[1].astype(np.uint8)

    smoothed = cv2.GaussianBlur(image, (5, 5), 0)
    canny = cv2.Canny(smoothed, 50, 150)
    line_image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)
    min_line_length = max(10, min(image.shape) // 8)
    hough_lines = cv2.HoughLinesP(
        canny,
        rho=1,
        theta=np.pi / 180,
        threshold=max(10, min(image.shape) // 8),
        minLineLength=min_line_length,
        maxLineGap=max(3, min(image.shape) // 50),
    )
    if hough_lines is not None:
        for x1, y1, x2, y2 in hough_lines.reshape(-1, 4):
            cv2.line(line_image, (x1, y1), (x2, y2), (255, 0, 0), 2)

    gx = cv2.Sobel(image, cv2.CV_32F, 1, 0, ksize=3)
    gy = cv2.Sobel(image, cv2.CV_32F, 0, 1, ksize=3)
    magnitude = cv2.magnitude(gx, gy)
    magnitude = cv2.normalize(
        magnitude, None, 0, 255, cv2.NORM_MINMAX
    ).astype(np.uint8)
    sobel_edges = cv2.threshold(
        magnitude, 100, 255, cv2.THRESH_BINARY
    )[1]

    return {
        "Original": image,
        "Min-max contrast": stretched,
        "Histogram equalization": equalized,
        "Point detection (Laplacian)": points,
        "Line detection (Hough)": line_image,
        "Sobel edges": sobel_edges,
        "Canny edges": canny,
        "Sobel gradient magnitude": magnitude,
    }


def make_test_images(image):
    """Build repeatable low-contrast, noisy, and blurred test samples."""
    rng = np.random.default_rng(4)
    low_contrast = np.clip(
        image.astype(np.float32) * 0.35 + 80, 0, 255
    ).astype(np.uint8)
    noisy = np.clip(
        image.astype(np.float32) + rng.normal(0, 20, image.shape), 0, 255
    ).astype(np.uint8)
    blurred = cv2.GaussianBlur(image, (9, 9), 0)
    return {
        "Original sample": image,
        "Low contrast": low_contrast,
        "Noisy": noisy,
        "Blurred": blurred,
    }


class ImageProcessingApp:
    def __init__(self, root, image):
        self.root = root
        self.root.title("Image processing — variant 4")
        self.root.geometry("1400x900")
        self.samples = make_test_images(image)
        self.current_image = image

        controls = ttk.Frame(root, padding=10)
        controls.pack(fill=tk.X)
        ttk.Label(controls, text="Test image:").pack(side=tk.LEFT)
        self.sample_name = tk.StringVar(value="Original sample")
        self.sample_picker = ttk.Combobox(
            controls,
            textvariable=self.sample_name,
            values=list(self.samples),
            state="readonly",
            width=24,
        )
        self.sample_picker.pack(side=tk.LEFT, padx=(8, 16))
        self.sample_picker.bind("<<ComboboxSelected>>", self.select_sample)
        ttk.Button(
            controls, text="Open image…", command=self.open_image
        ).pack(side=tk.LEFT)
        self.summary = tk.StringVar()
        ttk.Label(root, textvariable=self.summary, padding=(10, 0)).pack(
            fill=tk.X
        )

        self.figure = Figure(figsize=(14, 8), constrained_layout=True)
        self.canvas = FigureCanvasTkAgg(self.figure, master=root)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.show_results()

    def select_sample(self, _event=None):
        self.current_image = self.samples[self.sample_name.get()]
        self.show_results()

    def open_image(self):
        path = filedialog.askopenfilename(
            title="Choose an image",
            filetypes=[
                ("Image files", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return
        try:
            image = read_grayscale(path)
        except (OSError, ValueError, cv2.error) as error:
            messagebox.showerror("Unable to open image", str(error))
            return

        self.current_image = image
        self.sample_name.set(Path(path).name)
        self.show_results()

    def show_results(self):
        results = analyze_image(self.current_image)
        self.figure.clear()
        axes = self.figure.subplots(3, 3)
        for axis, (title, result) in zip(axes.flat[:8], results.items()):
            if result.ndim == 3:
                axis.imshow(result)
            else:
                axis.imshow(result, cmap="gray", vmin=0, vmax=255)
            axis.set_title(title)
            axis.axis("off")

        histogram_axis = axes.flat[8]
        for image, label, color in (
            (self.current_image, "Original", "gray"),
            (minmax_stretch(self.current_image), "Min-max", "green"),
            (cv2.equalizeHist(self.current_image), "Equalized", "blue"),
        ):
            histogram_axis.hist(
                image.ravel(),
                bins=256,
                range=(0, 256),
                color=color,
                alpha=0.35,
                label=label,
            )
        histogram_axis.set_title("Intensity histograms")
        histogram_axis.set_xlim(0, 256)
        histogram_axis.set_xlabel("Intensity")
        histogram_axis.set_ylabel("Pixel count")
        cdf = np.histogram(
            self.current_image.ravel(), bins=256, range=(0, 256)
        )[0].cumsum()
        cdf_axis = histogram_axis.twinx()
        cdf_axis.plot(
            np.arange(256), cdf / cdf[-1], color="red", linewidth=1,
            label="Original CDF",
        )
        cdf_axis.set_ylim(0, 1)
        cdf_axis.set_ylabel("Normalized CDF", color="red")
        histogram_handles, histogram_labels = (
            histogram_axis.get_legend_handles_labels()
        )
        cdf_handles, cdf_labels = cdf_axis.get_legend_handles_labels()
        histogram_axis.legend(
            histogram_handles + cdf_handles,
            histogram_labels + cdf_labels,
            fontsize="small",
        )

        self.figure.suptitle(
            "Variant 4: contrast enhancement and segmentation", fontsize=14
        )
        self.canvas.draw_idle()
        self.summary.set(
            f"{self.sample_name.get()} | "
            f"{self.current_image.shape[1]}×{self.current_image.shape[0]} px | "
            f"min={self.current_image.min()} "
            f"max={self.current_image.max()} "
            f"mean={self.current_image.mean():.1f} "
            f"std={self.current_image.std():.1f}"
        )

def main():
    image = read_grayscale(DEFAULT_IMAGE)
    root = tk.Tk()
    ImageProcessingApp(root, image)
    root.mainloop()


if __name__ == "__main__":
    main()
