import vapoursynth as vs
import cv2
import numpy as np
import insightface
import sys
import os

video_input = os.environ.get("VIDEO_INPUT")
image_target = os.environ.get("IMAGE_TARGET")
image_new = os.environ.get("IMAGE_NEW")
model_path = "inswapper_128.onnx"

core = vs.core

analyzer = insightface.app.FaceAnalysis(name='buffalo_l', providers=['CUDAExecutionProvider'])
analyzer.prepare(ctx_id=0, det_size=(640, 640), det_thresh=0.20)

img_target_mat = cv2.imread(image_target)
img_new_mat = cv2.imread(image_new)

if img_target_mat is None:
    sys.stderr.write(f"\n[FATAL ERROR] Cannot read target image: {image_target}.\n")
    sys.exit(1)
if img_new_mat is None:
    sys.stderr.write(f"\n[FATAL ERROR] Cannot read new image: {image_new}.\n")
    sys.exit(1)

target_faces = analyzer.get(img_target_mat)
new_faces = analyzer.get(img_new_mat)

if len(target_faces) == 0 or len(new_faces) == 0:
    sys.stderr.write(f"\n[FATAL ERROR] InsightFace detected ZERO faces in source images.\n")
    sys.exit(1)

target_face = target_faces[0]
new_face = new_faces[0]

clip = core.lsmas.LWLibavSource(source=video_input)
clip = core.resize.Bicubic(clip, format=vs.RGB24)

swapper = insightface.model_zoo.get_model(model_path, providers=['CUDAExecutionProvider'])

global_last_known_bbox = None

def process_frame(n, f):
    global global_last_known_bbox
    
    frame_array = np.dstack([np.asarray(f[i]) for i in range(3)])
    frame_bgr = cv2.cvtColor(frame_array, cv2.COLOR_RGB2BGR)

    faces_in_frame = analyzer.get(frame_bgr)
    
    best_face = None
    highest_sim = 0
    
    for face in faces_in_frame:
        similarity = np.dot(face.embedding, target_face.embedding) / (np.linalg.norm(face.embedding) * np.linalg.norm(target_face.embedding))
        if similarity > highest_sim:
            highest_sim = similarity
            best_face = face

    if highest_sim > 0.30:
        frame_bgr = swapper.get(frame_bgr, best_face, new_face, paste_back=True)
        global_last_known_bbox = best_face.bbox
        sys.stderr.write(f"Frame {n} | CLEAN MATCH: {highest_sim:.4f} | Memory Updated\n")
        
    elif global_last_known_bbox is not None and highest_sim > 0.15:
        closest_distance = float('inf')
        closest_face = None
        
        mem_x = (global_last_known_bbox[0] + global_last_known_bbox[2]) / 2
        mem_y = (global_last_known_bbox[1] + global_last_known_bbox[3]) / 2
        
        for face in faces_in_frame:
            face_x = (face.bbox[0] + face.bbox[2]) / 2
            face_y = (face.bbox[1] + face.bbox[3]) / 2
            
            dist = np.sqrt((mem_x - face_x)**2 + (mem_y - face_y)**2)
            if dist < closest_distance:
                closest_distance = dist
                closest_face = face
                
        if closest_face is not None and closest_distance < 150:
            frame_bgr = swapper.get(frame_bgr, closest_face, new_face, paste_back=True)
            global_last_known_bbox = closest_face.bbox  
            sys.stderr.write(f"Frame {n} | MATH FAILED: {highest_sim:.4f} | OVERRIDE: Using Location Tracking\n")
        else:
            sys.stderr.write(f"Frame {n} | MATH FAILED: {highest_sim:.4f} | Target Lost\n")
            global_last_known_bbox = None
    else:
        sys.stderr.write(f"Frame {n} | Target Not Found or Similarity Deep Drop ({highest_sim:.4f})\n")
        global_last_known_bbox = None
        
    sys.stderr.flush()

    frame_rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
    
    out_f = f.copy()
    for i in range(3):
        np.copyto(np.asarray(out_f[i]), frame_rgb[:, :, i])
        
    return out_f

swapped_clip = core.std.ModifyFrame(clip, clip, process_frame)
swapped_clip = core.resize.Bicubic(swapped_clip, format=vs.YUV420P8, matrix_s="709")
swapped_clip.set_output()
