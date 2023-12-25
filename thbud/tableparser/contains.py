import cv2

def has_table(image):
  # https://stackoverflow.com/questions/7227074/horizontal-line-detection-with-opencv
  # result = image.copy()
  # Load image, convert to grayscale, Otsu's threshold
  gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
  thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]

  # Detect vertical lines
  vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1,10))
  detect_vertical = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
  contours, hierarchy = cv2.findContours(detect_vertical, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
  for c in contours:
      x, y, w, h = cv2.boundingRect(c)
      if h > 80: return True
      # cv2.drawContours(result, [c], -1, (255, 0, 0), 2)

  return False