import os
from PIL import Image, ImageDraw, ImageFont
import io

def create_placeholder_image(width, height, text, filename):
    # Create a new image with a gradient background
    image = Image.new('RGB', (width, height))
    draw = ImageDraw.Draw(image)
    
    # Create gradient background
    for y in range(height):
        r = int((y / height) * 0)  # Start with dark
        g = int((y / height) * 100)  # Add some green
        b = int((y / height) * 255)  # More blue at bottom
        for x in range(width):
            draw.point((x, y), fill=(r, g, b))
    
    # Add text
    try:
        font = ImageFont.truetype("arial.ttf", 40)
    except:
        font = ImageFont.load_default()
    
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    # Add white text
    draw.text((x, y), text, fill='white', font=font)
    
    # Save the image
    image.save(filename)

def setup_images():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    static_dir = os.path.join(base_dir, 'static')
    images_dir = os.path.join(static_dir, 'images')
    leadership_dir = os.path.join(images_dir, 'leadership')
    demo_dir = os.path.join(images_dir, 'demo')
    
    # Create directories if they don't exist
    for directory in [static_dir, images_dir, leadership_dir, demo_dir]:
        if not os.path.exists(directory):
            os.makedirs(directory)
    
    # Create placeholder images for leadership
    placeholders = {
        'director.jpg': (400, 500, 'Director'),
        'principal.jpg': (400, 500, 'Principal'),
        'science-head.jpg': (300, 400, 'Science Head'),
        'math-head.jpg': (300, 400, 'Math Head'),
        'lang-head.jpg': (300, 400, 'Language Head'),
        'social-head.jpg': (300, 400, 'Social Science Head')
    }
    
    for filename, (width, height, text) in placeholders.items():
        filepath = os.path.join(leadership_dir, filename)
        create_placeholder_image(width, height, text, filepath)
    
    # Create school logo placeholder
    logo_path = os.path.join(images_dir, 'logo.png')
    create_placeholder_image(200, 200, 'LOGO', logo_path)
    
    # Create favicon
    favicon_path = os.path.join(images_dir, 'favicon.png')
    create_placeholder_image(32, 32, '', favicon_path)
    
    print("All placeholder images have been created successfully!")
    print("\nTo add your school's real logo:")
    print(f"1. Replace {logo_path} with your school's logo")
    print(f"2. Replace {favicon_path} with your school's favicon")
    print("\nTo add real staff photos:")
    print(f"Replace placeholder images in {leadership_dir} with actual photos")
    print("\nImage dimensions:")
    print("- Logo: 200x200 pixels (PNG format recommended)")
    print("- Favicon: 32x32 pixels (PNG format)")
    print("- Leadership photos: Keep the same dimensions as placeholders")

if __name__ == "__main__":
    setup_images()
