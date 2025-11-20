from PIL import Image

# Create a simple 100x100 red image
img = Image.new('RGB', (100, 100), color = 'red')
img.save('sample.png')
print("Created sample.png")
