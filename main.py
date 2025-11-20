import argparse
import os
import sys
from getpass import getpass

import stego
import crypto

def main():
    parser = argparse.ArgumentParser(description="Invisible Ink: Hide messages in images.")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Hide Command
    hide_parser = subparsers.add_parser("hide", help="Hide a message in an image")
    hide_parser.add_argument("image", help="Path to the source image")
    hide_parser.add_argument("--message", "-m", help="Message to hide (will prompt if not provided)")
    hide_parser.add_argument("--output", "-o", help="Path to save the output image (default: hidden.png)", default="hidden.png")
    hide_parser.add_argument("--password", "-p", help="Password to encrypt the message (optional)")
    
    # Reveal Command
    reveal_parser = subparsers.add_parser("reveal", help="Reveal a message from an image")
    reveal_parser.add_argument("image", help="Path to the image with hidden message")
    reveal_parser.add_argument("--password", "-p", help="Password to decrypt the message (optional)")
    
    args = parser.parse_args()
    
    if args.command == "hide":
        # 1. Get the message
        message = args.message
        if not message:
            print("Enter the message to hide:")
            message = sys.stdin.readline().strip()
            
        # 2. Encrypt if password provided
        if args.password:
            print("Encrypting message...")
            try:
                message = crypto.encrypt(message, args.password)
                # Mark that it's encrypted so we know to look for a password when decoding?
                # Ideally we'd add a flag in the data, but for now we rely on the user knowing.
                # To make it safer, let's prefix with "ENC:" so the decoder knows.
                message = "ENC:" + message
            except Exception as e:
                print(f"Encryption failed: {e}")
                return

        # 3. Hide the message
        try:
            stego.encode_message(args.image, message, args.output)
            print(f"Success! Output saved to {args.output}")
        except Exception as e:
            print(f"Error hiding message: {e}")
            
    elif args.command == "reveal":
        # 1. Extract hidden data
        try:
            hidden_data = stego.decode_message(args.image)
        except Exception as e:
            print(f"Error reading image: {e}")
            return
            
        if not hidden_data:
            print("No hidden message found (or image is corrupted).")
            return
            
        # 2. Check if encrypted
        if hidden_data.startswith("ENC:"):
            encrypted_content = hidden_data[4:] # Remove "ENC:" prefix
            
            password = args.password
            if not password:
                password = getpass("This message is encrypted. Enter password: ")
                
            try:
                decrypted = crypto.decrypt(encrypted_content, password)
                print("\n--- HIDDEN MESSAGE ---")
                print(decrypted)
                print("----------------------")
            except Exception:
                print("Error: Wrong password or corrupted data.")
        else:
            # Not encrypted (or at least not by us with the "ENC:" prefix)
            print("\n--- HIDDEN MESSAGE ---")
            print(hidden_data)
            print("----------------------")
            
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
