import cv2
import numpy as np
from matplotlib import pyplot as plt

# ---------- 1. Загрузка ----------
img = cv2.imread('data/image.png', cv2.IMREAD_GRAYSCALE)
assert img is not None, "file could not be read, check path"

# ---------- 2. Min-Max Stretching (линейное контрастирование) ----------
def minmax_stretch(image, out_min=0, out_max=255):
    in_min = np.min(image)
    in_max = np.max(image)
    # защита от деления на 0 (однородное изображение)
    if in_max == in_min:
        return np.full_like(image, out_min)
    stretched = (image.astype(np.float32) - in_min) * \
                (out_max - out_min) / (in_max - in_min) + out_min
    return np.clip(stretched, out_min, out_max).astype(np.uint8)

stretched = minmax_stretch(img, 0, 255)

# ---------- 3. Эквализация гистограммы ----------
equ = cv2.equalizeHist(img)

# ---------- 4. Градиенты Собеля и пороговая бинаризация ----------
gx = cv2.Sobel(img, cv2.CV_32F, 1, 0, ksize=3)
gy = cv2.Sobel(img, cv2.CV_32F, 0, 1, ksize=3)
magnitude = cv2.magnitude(gx, gy)
magnitude = cv2.normalize(magnitude, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
edges = cv2.threshold(magnitude, 100, 255, cv2.THRESH_BINARY)[1]

# ---------- 5. Детектор Кэнни ----------
canny = cv2.Canny(img, 100, 200)

# ---------- 6. Визуализация изображений ----------
titles = ['Original', 'Min-Max Stretch', 'Equalized',
          'Sobel edges', 'Canny', 'Histogram of gradients']
images = [img, stretched, equ, edges, canny, magnitude]

plt.figure(figsize=(14, 9))
for i, (im, t) in enumerate(zip(images, titles), 1):
    plt.subplot(2, 3, i)
    plt.imshow(im, cmap='gray', vmin=0, vmax=255)
    plt.title(t)
    plt.axis('off')
plt.tight_layout()
plt.show()

# ---------- 7. Сравнение гистограмм ----------
plt.figure(figsize=(14, 4))

for i, (im, t, c) in enumerate(zip(
        [img, stretched, equ],
        ['Original', 'Min-Max Stretch', 'Equalized'],
        ['gray', 'g', 'b']), 1):
    plt.subplot(1, 3, i)
    plt.hist(im.flatten(), 256, [0, 256], color=c, alpha=0.8)
    plt.xlim([0, 256])
    plt.title(f'Histogram: {t}')
    plt.xlabel('Intensity')
    plt.ylabel('Count')

plt.tight_layout()
plt.show()

# ---------- 8. Гистограмма + CDF для оригинала ----------
hist, bins = np.histogram(img.flatten(), 256, [0, 256])
cdf = hist.cumsum()
cdf_norm = cdf / cdf.max()

fig, ax1 = plt.subplots(figsize=(8, 5))
ax1.hist(img.flatten(), 256, [0, 256], color='r', alpha=0.7)
ax1.set_xlim([0, 256])
ax1.set_xlabel('Intensity')
ax1.set_ylabel('Count', color='r')

ax2 = ax1.twinx()
ax2.plot(cdf_norm, color='b')
ax2.set_ylim([0, 1])
ax2.set_ylabel('CDF (normalized)', color='b')

plt.title('Histogram and CDF (Original)')
plt.legend(['CDF', 'Histogram'], loc='upper left')
plt.show()

# ---------- 9. Числовое сравнение ----------
def stats(im, name):
    print(f"{name:18s} | min={im.min():3d} max={im.max():3d} "
          f"mean={im.mean():6.2f} std={im.std():6.2f}")

print("=== Статистика яркости ===")
stats(img, "Original")
stats(stretched, "Min-Max Stretch")
stats(equ, "Equalized")