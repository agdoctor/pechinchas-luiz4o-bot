import os
from PIL import Image, ImageOps

def apply_watermark(base_image_path: str, watermark_path: str = "watermark.png") -> str:
    """
    Applies a watermark frame to the base image.
    The script will center the product photo inside a white canvas matching the frame size,
    and overlay the frame on top.
    """
    if not os.path.exists(base_image_path) or not os.path.exists(watermark_path):
        return base_image_path
        
    # Ignora o arquivo se ele estiver vazio (como nosso placeholder)
    if os.path.getsize(watermark_path) < 100:
        return base_image_path
        
    try:
        base_img = Image.open(base_image_path).convert("RGBA")
        frame = Image.open(watermark_path)
        # Converte o frame para RGBA caso não seja
        frame = frame.convert("RGBA")
        
        # Se o frame não tem transparência real (é tudo opaco), transformamos o branco em transparente
        # Isso ajuda se o usuário salvou um PNG sem alfa ou um JPG por engano.
        datas = frame.getdata()
        new_data = []
        for item in datas:
            # Se for branco puro (ou quase branco para evitar compressão), torna transparente
            if item[0] > 245 and item[1] > 245 and item[2] > 245:
                new_data.append((255, 255, 255, 0))
            else:
                new_data.append(item)
        frame.putdata(new_data)
        
        # O tamanho final será exatamente igual ao tamanho do frame
        frame_w, frame_h = frame.size
        
        # Cria um canvas com fundo branco sólido
        canvas = Image.new("RGBA", (frame_w, frame_h), (255, 255, 255, 255))
        
        # Redimensiona a foto do produto (90% do tamanho para zoom out)
        zoom_factor = 0.90
        target_size = (int(frame_w * zoom_factor), int(frame_h * zoom_factor))
        base_img.thumbnail(target_size, Image.Resampling.LANCZOS)
        
        # Centraliza
        pos_x = (frame_w - base_img.width) // 2
        pos_y = (frame_h - base_img.height) // 2
        
        # Cola o produto no canvas
        canvas.paste(base_img, (pos_x, pos_y), base_img if base_img.mode == 'RGBA' else None)
        
        # Cola o Frame transparente por cima
        canvas.paste(frame, (0, 0), frame)
        
        new_path = base_image_path.rsplit('.', 1)[0] + "_wm.png"
        canvas.save(new_path, "PNG")
        
        return new_path
        
    except Exception as e:
        print(f"Erro ao aplicar frame: {e}")
        return base_image_path
