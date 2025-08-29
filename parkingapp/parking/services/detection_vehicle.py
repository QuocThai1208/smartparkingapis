from ..models import Vehicle
import numpy as np
import  requests
import torch
import cv2
from torchreid.reid.utils.feature_extractor import FeatureExtractor
from PIL import Image
from io import BytesIO

# Load model OSNet (GPU)
extractor = FeatureExtractor(model_name='osnet_x1_0', device='cpu')


# Hàm color histogram
def extract_color_histogram_from_array(image, bins=(8,8,8)):
    image = cv2.cvtColor(image, cv2.COLOR_RGB2HSV) # Chuyển ảnh từ GRB sang HSV
    hist = cv2.calcHist([image], [0,1,2], None, bins, [0,180,0,256,0,256]) # tính giá trị Histogram
    cv2.normalize(hist, hist) # chuẩn hóa về L2
    return hist.flatten() # Chuyển thành vector 1D


# Hàm so sánh 2 ảnh
def check_vehicle(img1, img2):
    response = requests.get(img1.url)
    img1 = Image.open(BytesIO(response.content)).convert('RGB')
    img1 = np.array(img1)

    img2 = cv2.imread(img2)
    img2 = cv2.cvtColor(img2, cv2.COLOR_BGR2RGB)

    emb1 = extractor([img1])[0]
    emb2 = extractor([img2])[0]

    color1 = extract_color_histogram_from_array(img1)
    color2 = extract_color_histogram_from_array(img2)

    sim_emb = torch.nn.functional.cosine_similarity(emb1, emb2, dim=0)
    sim_emb = sim_emb.item()

    sim_color = np.dot(color1, color2) / (np.linalg.norm(color1) * np.linalg.norm(color2))

    if sim_emb > 0.8 and sim_color > 0.9:
        return True, "Xe hợp lệ."
    return False,  "Phát hiện gian lận biển số."



