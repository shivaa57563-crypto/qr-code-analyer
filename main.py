import cv2
from pyzbar.pyzbar import decode

# Load image
image_path = "qr_code.png"  # replace with your image file
img = cv2.imread(image_path)

# Decode QR codes
decoded_objects = decode(img)

# Check and display results
if decoded_objects:
    for obj in decoded_objects:
        data = obj.data.decode("utf-8")
        print("QR Code Data:", data)

        # Draw rectangle around QR code
        points = obj.polygon
        if len(points) == 4:
            pts = [(point.x, point.y) for point in points]
            for i in range(4):
                cv2.line(img, pts[i], pts[(i+1) % 4], (0, 255, 0), 2)

        # Display decoded text on image
        cv2.putText(img, data, (obj.rect.left, obj.rect.top - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Show image
    cv2.imshow("QR Code Scanner", img)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

else:
    print("No QR Code found!")
