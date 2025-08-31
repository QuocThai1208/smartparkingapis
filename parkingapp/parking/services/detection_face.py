import cv2
from insightface.app import FaceAnalysis
import numpy as np
from django.db import transaction
from ..models import UserFace
import requests


app = FaceAnalysis(name="buffalo_l")  # bộ model đã train gồm detector face và recognizer face
app.prepare(ctx_id=0, det_size=(640, 640))


# hàm so sách embedding
def cosine_similarity(vec1, vec2):
    # Chuyển thành mảng numpy
    v1 = np.array(vec1)
    v2 = np.array(vec2)
    # trả về kết quả tích vô hướng
    return np.dot(v1, v2)


@transaction.atomic
def find_or_create_user_face(new_embedding, face_img=None, threshold=0.6):
    new_emb = np.array(new_embedding)

    for user_face in UserFace.objects.all():
        if not user_face.embedding:
            continue
        emb = user_face.embedding
        sim = cosine_similarity(new_emb, emb)
        if sim >= threshold:
            update_emb = ((emb + new_emb) / 2).tolist()
            user_face.embedding = update_emb
            user_face.face_img = face_img
            user_face.save()
            return user_face

    user_face = UserFace.objects.create(
        face_img=face_img,
        embedding=new_emb.tolist()
    )
    return user_face


def math_emb(img):
    img1 = cv2.imread(img)
    faces1 = app.get(img1)
    if len(faces1) > 0:
        emb = faces1[0].normed_embedding
        return emb
