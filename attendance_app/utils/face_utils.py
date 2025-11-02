# import face_recognition
import cv2
import numpy as np
import os
from deepface import DeepFace
import os

def recognize_face(image_path, faces_folder='faces'):
    for file in os.listdir(faces_folder):
        if file.endswith(('.jpg', '.jpeg', '.png')):
            registered_path = os.path.join(faces_folder, file)
            result = DeepFace.verify(img1_path=image_path, img2_path=registered_path, enforce_detection=False)
            if result['verified']:
                return file.split('_')[0]
    return None


def is_face_already_registered(new_image_path, faces_folder='faces', threshold=0.7):
    """
    Compare the new image against all registered faces.
    Returns (True, matched_name) if found, else (False, None)
    """
    for file in os.listdir(faces_folder):
        if file.endswith(('.jpg', '.jpeg', '.png')):
            registered_path = os.path.join(faces_folder, file)
            try:
                result = DeepFace.verify(
                    img1_path=new_image_path,
                    img2_path=registered_path,
                    model_name='Facenet',     # faster than VGGFace
                    enforce_detection=False
                )
                if result['verified'] and result['distance'] < threshold:
                    # Found a match
                    matched_name = file.split('_')[0]
                    return True, matched_name
            except Exception as e:
                print("⚠️ Error comparing faces:", e)
                continue
    return False, None