from PIL import Image

# We use a delimiter to mark the end of our message.
# When decoding, we stop reading bits once we see this pattern.
DELIMITER = "#####"

def str_to_bin(message):
    """
    Converts a string to its binary representation.
    Example: "Hi" -> "0100100001101001"
    """
    # ord(char) gets the ASCII value (e.g., 'A' is 65).
    # format(..., '08b') converts it to an 8-bit binary string (e.g., 65 -> '01000001').
    return ''.join(format(ord(char), '08b') for char in message)

def bin_to_str(binary_data):
    """
    Converts a binary string back to text.
    """
    all_chars = []
    # Process 8 bits at a time
    for i in range(0, len(binary_data), 8):
        byte = binary_data[i:i+8]
        if len(byte) < 8:
            break
        # int(byte, 2) converts binary '01000001' back to integer 65.
        # chr(65) converts it back to 'A'.
        all_chars.append(chr(int(byte, 2)))
    return ''.join(all_chars)

def encode_message(image_path, message, output_path):
    """
    Hides a message inside an image using LSB steganography.
    """
    # 1. Open the image.
    img = Image.open(image_path)
    # Convert to RGB to ensure we have 3 channels per pixel.
    img = img.convert("RGB")
    
    # 2. Prepare the message.
    # We append the delimiter so we know when to stop reading later.
    full_message = message + DELIMITER
    binary_message = str_to_bin(full_message)
    message_len = len(binary_message)
    
    # 3. Check if the image is big enough.
    # Each pixel has 3 values (R, G, B), so we can store 3 bits per pixel.
    width, height = img.size
    max_bits = width * height * 3
    
    if message_len > max_bits:
        raise ValueError(f"Message is too long for this image! Need {message_len} bits, have {max_bits}.")
    
    print(f"Hiding {message_len} bits in a {width}x{height} image...")
    
    # 4. Modify the pixels.
    pixels = img.load()
    data_index = 0
    
    for y in range(height):
        for x in range(width):
            if data_index >= message_len:
                break
                
            r, g, b = pixels[x, y]
            
            # Modify Red channel LSB
            if data_index < message_len:
                # (r & ~1) clears the last bit (makes it 0).
                # | int(...) sets the last bit to our message bit (0 or 1).
                r = (r & ~1) | int(binary_message[data_index])
                data_index += 1
                
            # Modify Green channel LSB
            if data_index < message_len:
                g = (g & ~1) | int(binary_message[data_index])
                data_index += 1
                
            # Modify Blue channel LSB
            if data_index < message_len:
                b = (b & ~1) | int(binary_message[data_index])
                data_index += 1
                
            # Update the pixel with modified values
            pixels[x, y] = (r, g, b)
        
        if data_index >= message_len:
            break
            
    # 5. Save the result.
    # We use PNG because it's lossless. JPEG compression would destroy our LSB data!
    img.save(output_path, "PNG")
    print(f"Message hidden successfully in {output_path}")

def decode_message(image_path):
    """
    Extracts the hidden message from an image.
    """
    img = Image.open(image_path)
    img = img.convert("RGB")
    
    binary_data = ""
    pixels = img.load()
    width, height = img.size
    
    # Iterate through pixels and read LSBs
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            
            # Extract LSB from each channel
            binary_data += str(r & 1)
            binary_data += str(g & 1)
            binary_data += str(b & 1)
            
    # Convert binary to string
    # We do this in chunks to check for the delimiter early
    all_chars = []
    for i in range(0, len(binary_data), 8):
        byte = binary_data[i:i+8]
        if len(byte) < 8:
            break
        char = chr(int(byte, 2))
        all_chars.append(char)
        
        # Check if we've found the delimiter at the end of our reconstructed string
        current_message = "".join(all_chars)
        if current_message.endswith(DELIMITER):
            # Return the message without the delimiter
            return current_message[:-len(DELIMITER)]
            
    # If we processed the whole image and didn't find the delimiter, something is wrong.
    return ""
