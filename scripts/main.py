import cv2
import numpy as np
from matplotlib import pyplot as plt

img = cv2.imread('data/image.png', cv2.IMREAD_GRAYSCALE)

equ = cv2.equalizeHist(img)
gx = cv2.Sobel(img, cv2.CV_32F, 1, 0, ksize=3)
gy = cv2.Sobel(img, cv2.CV_32F, 0, 1, ksize=3)
magnitude = cv2.magnitude(gx, gy)

edges = (magnitude > 100).astype(np.uint8) * 255

canny = cv2.Canny(img, 100, 200)

result = np.hstack((img, equ))
assert img is not None, "file could not be read, check with os.path.exists()"
hist,bins = np.histogram(result.flatten(),256,[0,256])
cdf = hist.cumsum()
cdf_normalized = cdf * float(hist.max()) / cdf.max()
plt.plot(cdf_normalized, color = 'b')
plt.hist(img.flatten(),256,[0,256], color = 'r')
plt.xlim([0,256])
plt.legend(('cdf','histogram'), loc = 'upper left')
plt.show()