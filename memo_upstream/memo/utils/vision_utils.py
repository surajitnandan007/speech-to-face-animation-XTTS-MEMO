import logging

import cv2
import numpy as np
import torch
from moviepy.editor import AudioFileClip, VideoClip
from PIL import Image
from torchvision import transforms

try:
    from insightface.app import FaceAnalysis
except ModuleNotFoundError:  # pragma: no cover - optional dependency
    FaceAnalysis = None


logger = logging.getLogger(__name__)


def tensor_to_video(tensor, output_video_path, input_audio_path, fps=30):
    """
    Converts a Tensor with shape [c, f, h, w] into a video and adds an audio track from the specified audio file.

    Args:
        tensor (Tensor): The Tensor to be converted, shaped [c, f, h, w].
        output_video_path (str): The file path where the output video will be saved.
        input_audio_path (str): The path to the audio file (WAV file) that contains the audio track to be added.
        fps (int): The frame rate of the output video. Default is 30 fps.
    """
    tensor = tensor.permute(1, 2, 3, 0).cpu().numpy()  # convert to [f, h, w, c]
    tensor = np.clip(tensor * 255, 0, 255).astype(np.uint8)  # to [0, 255]

    def make_frame(t):
        frame_index = min(int(t * fps), tensor.shape[0] - 1)
        return tensor[frame_index]

    video_duration = tensor.shape[0] / fps
    audio_clip = AudioFileClip(input_audio_path)
    audio_duration = audio_clip.duration
    final_duration = min(video_duration, audio_duration)
    audio_clip = audio_clip.subclip(0, final_duration)
    new_video_clip = VideoClip(make_frame, duration=final_duration)
    new_video_clip = new_video_clip.set_audio(audio_clip)
    new_video_clip.write_videofile(output_video_path, fps=fps, audio_codec="aac")


@torch.no_grad()
def preprocess_image(face_analysis_model: str, image_path: str, image_size: int = 512):
    """
    Preprocess the image and extract face embedding.

    Args:
        face_analysis_model (str): Path to the FaceAnalysis model directory.
        image_path (str): Path to the image file.
        image_size (int, optional): Target size for resizing the image. Default is 512.

    Returns:
        tuple: A tuple containing:
            - pixel_values (torch.Tensor): Tensor of the preprocessed image.
            - face_emb (torch.Tensor): Tensor of the face embedding.
    """
    # Define the image transformation
    transform = transforms.Compose(
        [
            transforms.Resize((image_size, image_size)),
            transforms.ToTensor(),
            transforms.Normalize([0.5], [0.5]),
        ]
    )

    # Initialize the FaceAnalysis model
    # Load and preprocess the image
    image = Image.open(image_path).convert("RGB")
    pixel_values = transform(image)
    pixel_values = pixel_values.unsqueeze(0)

    faces = []
    if FaceAnalysis is not None:
        face_analysis = FaceAnalysis(
            name="",
            root=face_analysis_model,
            providers=["CUDAExecutionProvider", "CPUExecutionProvider"],
        )
        face_analysis.prepare(ctx_id=0, det_size=(640, 640))
        image_bgr = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        faces = face_analysis.get(image_bgr)
        del face_analysis
    else:
        logger.warning("insightface is not installed. Using a zero vector as the face embedding.")

    if not faces:
        logger.warning("No faces detected in the image. Using a zero vector as the face embedding.")
        face_emb = np.zeros(512)
    else:
        # Sort faces by size and select the largest one
        faces_sorted = sorted(
            faces,
            key=lambda x: (x["bbox"][2] - x["bbox"][0]) * (x["bbox"][3] - x["bbox"][1]),
            reverse=True,
        )
        face_emb = faces_sorted[0]["embedding"]

    # Convert face embedding to a PyTorch tensor
    face_emb = face_emb.reshape(1, -1)
    face_emb = torch.tensor(face_emb)

    return pixel_values, face_emb
